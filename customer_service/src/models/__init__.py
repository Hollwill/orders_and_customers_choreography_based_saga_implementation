import copy
import datetime
import logging

from sqlalchemy import func, Integer, ForeignKey, JSON, orm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.events import Event, CustomerCreditReservationEvent, CustomerCreditLimitExceededEvent, CustomerCreatedEvent
from src.schemas import OrderCreatedSchema

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class BaseClass:
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    deleted_at: Mapped[datetime.datetime | None]
    updated_at: Mapped[datetime.datetime | None] = mapped_column(
        default=func.now(),
        onupdate=func.current_timestamp(),
    )

class Versioned:
    version_id = mapped_column(Integer, nullable=False)

    __mapper_args__ = {"version_id_col": version_id}

class Eventable:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._domain_events: list[Event] = []

    @orm.reconstructor
    def init_on_load(self):
        self._domain_events: list[Event] = []

    @property
    def events(self) -> list[Event]:
        return self._domain_events[:]

    def _add_domain_event(self, event: Event) -> None:
        self._domain_events.append(event)


class Customer(Eventable, Base, BaseClass, Versioned, ):
    __tablename__ = "customers"

    name: Mapped[str]
    money_limit: Mapped[int]
    credit_reservations: Mapped[list["CreditReservation"]] = relationship(back_populates="customer", lazy="selectin",
                                                                          primaryjoin="and_(Customer.id == CreditReservation.customer_id, CreditReservation.deleted_at.is_(None))",)

    @staticmethod
    def create(name: str, money_limit: int) -> "Customer":
        customer = Customer(name=name, money_limit=money_limit)
        customer._add_domain_event(CustomerCreatedEvent(customer.money_limit, name=name))
        return customer

    def reserve_credit(self, order: OrderCreatedSchema):
        if order.order_total <= self.money_limit:
            self.credit_reservations.append(CreditReservation.create(order))
            self.money_limit -= order.order_total

            self._add_domain_event(CustomerCreditReservationEvent(order.aggregate_id))
        else:
            self._add_domain_event(CustomerCreditLimitExceededEvent(order.aggregate_id))

    def unreserve_credit(self, order_id):
        for credit_reservation in self.credit_reservations:
            if credit_reservation.order_id == order_id:
                credit_reservation.deleted_at = datetime.datetime.now()
                break

        else:
            logger.error(f"Credit reservation with order_id {order_id} for customer {self.id} not found")




class CreditReservation(Base, BaseClass):
    __tablename__ = "credit_reservations"

    order_id: Mapped[int]
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))

    customer: Mapped[Customer] = relationship(back_populates="credit_reservations")
    amount: Mapped[int]

    @staticmethod
    def create(order: OrderCreatedSchema) -> "CreditReservation":
        return CreditReservation(order_id=order.aggregate_id, amount=order.order_total)

class OutboxMessageModel(Base, BaseClass):
    __tablename__ = "outbox_messages"

    exchange: Mapped[str]
    key: Mapped[str]
    aggregate_id: Mapped[int]
    data: Mapped[dict] = mapped_column(type_=JSON)
    processed_on: Mapped[datetime.datetime | None] = mapped_column(default=None)


    def get_data_with_aggregate_id(self) -> dict:
        data_copy = copy.deepcopy(self.data)
        data_copy["aggregate_id"] = self.aggregate_id
        return data_copy

    @staticmethod
    def create(aggregate_id, event: "Event") -> "OutboxMessageModel":
        return OutboxMessageModel(aggregate_id=aggregate_id, exchange=event.exchange, key=event.key, data=event.data)

    def __repr__(self):
        return f"src.models.OutboxMessageModel ({self.data=} {self.exchange=} {self.key=})"
