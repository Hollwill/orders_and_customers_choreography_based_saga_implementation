import asyncio

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

from src.config import settings
from src.database import async_context_get_session
from src.schemas import OrderCreatedSchema, OrderCanceledSchema
from src.services import CustomerService, OutboxSaveService

broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)

order_exchange = RabbitExchange(name="order.order")

order_created_queue = RabbitQueue(name="customer.order_created")
order_canceled_queue = RabbitQueue(name="customer.order_canceled")


@broker.subscriber(order_created_queue)
async def order_created(order: OrderCreatedSchema):
    async with async_context_get_session() as session:

        service = CustomerService(session, OutboxSaveService(session))
        await service.reserve_credit(order)

@broker.subscriber(order_canceled_queue)
async def order_canceled(order_canceled_info: OrderCanceledSchema):
    async with async_context_get_session() as session:

        service = CustomerService(session, OutboxSaveService(session))
        await service.unreserve_credit(order_canceled_info)


@app.after_startup
async def declare_and_bind():
    robust_order_exchange = await broker.declare_exchange(order_exchange)

    robust_order_created_queue = await broker.declare_queue(order_created_queue)
    robust_order_canceled_queue = await broker.declare_queue(order_canceled_queue)

    await robust_order_created_queue.bind(robust_order_exchange, "order.created")
    await robust_order_canceled_queue.bind(robust_order_exchange, "order.canceled")



if __name__ == "__main__":
    asyncio.run(app.run())