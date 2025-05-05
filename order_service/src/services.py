import datetime
import logging

from fastapi import HTTPException
from faststream.exceptions import FastStreamException
from faststream.rabbit import RabbitBroker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.events import Event
from src.models import OutboxMessageModel, Order
from src.schemas import OrderCreateSchema, OrderSchema, CustomerNotFoundConsumerSchema, \
    CustomerCreditReservationConsumerSchema, CustomerCreditLimitExceededConsumerSchema

logger = logging.getLogger(__name__)

class BaseService:
    def __init__(self, session: AsyncSession, events_save_service: "OutboxSaveService"):
        self.session = session
        self.events_save_service = events_save_service

class OrderService(BaseService):
    async def create_order(self, order_in: OrderCreateSchema) -> Order:
        order = Order.create(customer_id=order_in.customer_id, order_total=order_in.order_total)

        self.session.add(order)
        await self.session.flush()

        await self.events_save_service.save(order.id, order.events)

        return order

    async def customer_not_found(self, customer_not_found_info: CustomerNotFoundConsumerSchema):
        stmt = select(Order).where(Order.id == customer_not_found_info.order_id and Order.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            logger.error(f"Order with id {customer_not_found_info.order_id} for customer {customer_not_found_info.aggregate_id} not found")
            return
        order.customer_not_found()
        await self.session.flush()

    async def customer_credit_reservation(self, credit_reservation_info: CustomerCreditReservationConsumerSchema):
        stmt = select(Order).where(Order.id == credit_reservation_info.order_id and Order.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            logger.error(f"Order with id {credit_reservation_info.order_id} for customer {credit_reservation_info.aggregate_id} not found")
            return
        order.credit_reservation()
        await self.session.flush()

    async def customer_credit_limit_exceeded(self, credit_limit_exceeded_info: CustomerCreditLimitExceededConsumerSchema):
        stmt = select(Order).where(Order.id == credit_limit_exceeded_info.order_id and Order.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            logger.error(f"Order with id {credit_limit_exceeded_info.order_id} for customer {credit_limit_exceeded_info.aggregate_id} not found")
            return
        order.credit_limit_exceeded()
        await self.session.flush()

    async def cancel_order(self, order_id: int):
        stmt = select(Order).where(Order.id == order_id and Order.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        order = result.scalar_one_or_none()
        if not order:
            logger.error(f"Order with id {order_id} not found")
            return
        order.cancel()
        await self.events_save_service.save(order.id, order.events)
        await self.session.flush()

    async def get_order_by_id(self, item_id) -> Order:
        result = await self.session.execute(select(Order).where(Order.id == item_id, Order.deleted_at.is_(None)))
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order


class OutboxSaveService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, aggregate_id: int, events: list[Event]):
        outbox_models = [OutboxMessageModel.create(aggregate_id, event) for event in events]
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
                logger.info("Published event: %s", event)
            except FastStreamException:
                logger.exception(f"Error publishing outbox message message_id {event.id}")
                continue
            event.processed_on = datetime.datetime.now()
            self.session.add(event)
