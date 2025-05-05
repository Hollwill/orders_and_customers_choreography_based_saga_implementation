import asyncio

from faststream import FastStream
from faststream.rabbit import RabbitExchange, RabbitQueue

from src.broker import get_broker
from src.database import async_context_get_session
from src.schemas import (CustomerNotFoundConsumerSchema, CustomerCreditReservationConsumerSchema,
                         CustomerCreditLimitExceededConsumerSchema)
from src.services import OutboxSaveService, OrderService

broker = get_broker()
app = FastStream(broker)

customer_exchange = RabbitExchange(name="customer.customer")

customer_not_found_queue = RabbitQueue(name="order.customer_not_found")
customer_credit_reservation_queue = RabbitQueue(name="order.customer_credit_reservation")
customer_credit_limit_exceeded_queue = RabbitQueue(name="order.customer_credit_limit_exceeded")


@broker.subscriber(customer_not_found_queue)
async def customer_not_found(order_info: CustomerNotFoundConsumerSchema):
    async with async_context_get_session() as session:
        service = OrderService(session, OutboxSaveService(session))
        await service.customer_not_found(order_info)


@broker.subscriber(customer_credit_reservation_queue)
async def credit_reservation(order_info: CustomerCreditReservationConsumerSchema):
    async with async_context_get_session() as session:
        service = OrderService(session, OutboxSaveService(session))
        await service.customer_credit_reservation(order_info)


@broker.subscriber(customer_credit_limit_exceeded_queue)
async def credit_limit_exceeded(order_info: CustomerCreditLimitExceededConsumerSchema):
    async with async_context_get_session() as session:
        service = OrderService(session, OutboxSaveService(session))
        await service.customer_credit_limit_exceeded(order_info)


@app.after_startup
async def declare_and_bind():
    robust_customer_exchange = await broker.declare_exchange(customer_exchange)

    robust_customer_not_found_queue = await broker.declare_queue(customer_not_found_queue)
    robust_customer_credit_reservation_queue = await broker.declare_queue(customer_credit_reservation_queue)
    robust_customer_credit_limit_exceeded_queue = await broker.declare_queue(customer_credit_limit_exceeded_queue)

    await robust_customer_not_found_queue.bind(robust_customer_exchange, "customer.customer_not_found")
    await robust_customer_credit_reservation_queue.bind(robust_customer_exchange,
                                                        "customer.customer_credit_reservation")
    await robust_customer_credit_limit_exceeded_queue.bind(robust_customer_exchange,
                                                           "customer.customer_credit_limit_exceeded")


if __name__ == "__main__":
    asyncio.run(app.run())
