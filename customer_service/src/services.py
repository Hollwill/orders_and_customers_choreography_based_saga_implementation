import datetime
import logging

from faststream.exceptions import FastStreamException
from faststream.rabbit import RabbitBroker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.events import Event, CustomerNotFoundEvent
from src.models import OutboxMessageModel, Customer
from src.schemas import CustomerCreateSchema, OrderCreatedSchema, OrderCanceledSchema

logger = logging.getLogger(__name__)

class BaseService:
    def __init__(self, session: AsyncSession, events_save_service: "OutboxSaveService"):
        self.session = session
        self.events_save_service = events_save_service

class CustomerService(BaseService):
    async def create_customer(self, customer_in: CustomerCreateSchema) -> Customer:
        customer = Customer.create(name=customer_in.name, money_limit=customer_in.money_limit)

        self.session.add(customer)
        await self.session.flush()

        await self.events_save_service.save(customer.id, customer.events)

        return customer

    async def reserve_credit(self, order: OrderCreatedSchema):

        stmt = select(Customer).where(Customer.id == order.customer_id and Customer.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        customer = result.scalar_one_or_none()
        if not customer:
            await self.events_save_service.save(order.customer_id, CustomerNotFoundEvent(order.aggregate_id))
            return

        customer.reserve_credit(order)
        await self.events_save_service.save(customer.id, customer.events)
        self.session.add(customer)
        await self.session.commit()

    async def unreserve_credit(self, order_canceled_info: OrderCanceledSchema):
        result = await self.session.execute(select(Customer).where(Customer.id == order_canceled_info.customer_id and Customer.deleted_at.is_(None)))
        customer = result.scalar_one_or_none()
        if not customer:
            logger.error(f"No customer found with id {order_canceled_info.customer_id}")
        customer.unreserve_credit(order_canceled_info.aggregate_id)


class OutboxSaveService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, aggregate_id: int, events: list[Event] | Event):
        if isinstance(events, Event):
            events = [events]
        outbox_models = [OutboxMessageModel.create(aggregate_id, event) for event in events]
        for i in outbox_models:
            logger.error("Saved event: %s", repr(i))
        self.session.add_all(outbox_models)

class OutboxPublishService:
    def __init__(self, session: AsyncSession, broker: RabbitBroker):
        self.session = session
        self.broker = broker

    async def publish_all(self):
        stmt = select(OutboxMessageModel).where(OutboxMessageModel.processed_on.is_(None))

        result = await self.session.execute(stmt)
        items = result.scalars().all()
        for event in items:
            try:
                await self.broker.publish(event.get_data_with_aggregate_id(), exchange=event.exchange, routing_key=event.key)
                logger.error("Published event: %s", repr(event))
            except FastStreamException:
                logger.exception(f"Error publishing outbox message message_id {event.id}")
                continue
            event.processed_on = datetime.datetime.now()
            self.session.add(event)
