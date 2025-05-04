import copy
import datetime
import logging
from decimal import Decimal

from sqlalchemy import func, Integer, ForeignKey, JSON, orm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.constants import OrderState, RejectionReason
from src.events import Event, OrderCreatedEvent, OrderCanceledEvent

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
    _domain_events: list[Event]

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


class Order(Eventable, Base, BaseClass, Versioned ):
    __tablename__ = "orders"

    state: Mapped[OrderState] = mapped_column(default=OrderState.PENDING)
    rejection_reason: Mapped[RejectionReason | None] = mapped_column(default=None)
    customer_id: Mapped[int]
    order_total: Mapped[int]


    @staticmethod
    def create(customer_id: int, order_total: int) -> "Order":
        order = Order(customer_id=customer_id ,order_total=order_total)
        order._add_domain_event(OrderCreatedEvent(customer_id, order_total))
        return order

    def customer_not_found(self):
        self.rejection_reason = RejectionReason.UNKNOWN_CUSTOMER
        self.state = OrderState.REJECTED

    def credit_reservation(self):
        self.state = OrderState.APPROVED

    def credit_limit_exceeded(self):
        self.state = OrderState.REJECTED
        self.rejection_reason = RejectionReason.INSUFFICIENT_CREDIT

    def cancel(self):
        if self.state != OrderState.APPROVED:
            logger.error(f"Order with id {self.id} cannot be cancelled")

        self.state = OrderState.CANCELLED
        self._add_domain_event(OrderCanceledEvent(self.customer_id))



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
