import asyncio
import logging

from faststream import Depends
from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from pymongo.asynchronous.collection import AsyncCollection

from src.config import settings
from src.constants import OrderState, RejectionReason
from src.database import get_order_history_collection
from src.schemas import CustomerCreatedSchema, OrderCreatedSchema, CreditReservationSchema

logger = logging.getLogger(__name__)

broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)

customer_exchange = RabbitExchange(name="customer.customer")
order_exchange = RabbitExchange(name="order.order")

customer_created_queue = RabbitQueue(name="order_history.customer_created")
customer_credit_reservation_queue = RabbitQueue(name="order_history.customer_credit_reservation")
customer_credit_limit_exceeded_queue = RabbitQueue(name="order_history.customer_credit_limit_exceeded")

order_created_queue = RabbitQueue(name="order_history.order_created")




@broker.subscriber(customer_created_queue)
async def customer_created(customer: CustomerCreatedSchema, collection: AsyncCollection = Depends(get_order_history_collection)):
    customer_document = {
        "_id": customer.aggregate_id,
        "name": customer.name,
        "money_limit": customer.money_limit,
        "orders": []
    }
    await collection.insert_one(customer_document)

@broker.subscriber(customer_credit_reservation_queue)
async def credit_reservation(customer_credit_reservation: CreditReservationSchema, collection: AsyncCollection = Depends(get_order_history_collection)):
    customer = await collection.find_one(customer_credit_reservation.aggregate_id)
    if not customer:
        logger.error(f"No customer with id {customer_credit_reservation.aggregate_id} found")

    for i, customer_order in enumerate(customer["orders"]):
        if customer_order["_id"] == customer_credit_reservation.order_id:
            order = customer_order
            order_idx = i
            break
    else:
        logger.error(f"Order with id {customer_credit_reservation.order_id} not found")
        return
    order_total = order["order_total"]

    await collection.update_one({"_id": customer_credit_reservation.aggregate_id}, {"$set": {"money_limit": customer["money_limit"] - order_total, f"orders.{order_idx}.state": OrderState.APPROVED.value}})

@broker.subscriber(customer_credit_limit_exceeded_queue)
async def credit_limit_exceeded(customer_credit_reservation: CreditReservationSchema, collection: AsyncCollection = Depends(get_order_history_collection)):
    customer = await collection.find_one(customer_credit_reservation.aggregate_id)
    if not customer:
        logger.error(f"No customer with id {customer_credit_reservation.aggregate_id} found")

    for i, customer_order in enumerate(customer["orders"]):
        if customer_order["_id"] == customer_credit_reservation.order_id:
            order_idx = i
            break
    else:
        logger.error(f"Order with id {customer_credit_reservation.order_id} not found")
        return

    await collection.update_one({"_id": customer_credit_reservation.aggregate_id}, {"$set": { f"orders.{order_idx}.state": OrderState.REJECTED.value, f"orders.{order_idx}.rejection_reason": RejectionReason.INSUFFICIENT_CREDIT.value}})

@broker.subscriber(order_created_queue)
async def order_created(order: OrderCreatedSchema, collection: AsyncCollection = Depends(get_order_history_collection)):
    customer = await collection.find_one()

    order_to_create = {
        "_id": order.aggregate_id,
        "order_total": order.order_total,
        "state": OrderState.PENDING.value,
        "rejection_reason": None,
    }

    await collection.update_one({"_id": customer["_id"]}, {"$push": {"orders": order_to_create}})


# @broker.subscriber(customer_credit_reservation_queue)
# async def credit_reservation(order_info: CustomerCreditReservationConsumerSchema):
#     async with async_context_get_session() as session:
#
#         service = OrderService(session, OutboxSaveService(session))
#         await service.customer_credit_reservation(order_info)
#
# @broker.subscriber(customer_credit_limit_exceeded_queue)
# async def credit_limit_exceeded(order_info: CustomerCreditLimitExceededConsumerSchema):
#     async with async_context_get_session() as session:
#
#         service = OrderService(session, OutboxSaveService(session))
#         await service.customer_credit_limit_exceeded(order_info)
#

@app.after_startup
async def declare_and_bind():
    robust_customer_exchange = await broker.declare_exchange(customer_exchange)
    robust_order_exchange = await broker.declare_exchange(order_exchange)

    robust_customer_created_queue = await broker.declare_queue(customer_created_queue)
    robust_customer_credit_reservation_queue = await broker.declare_queue(customer_credit_reservation_queue)
    robust_customer_credit_limit_exceeded_queue = await broker.declare_queue(customer_credit_limit_exceeded_queue)

    robust_order_created_queue = await broker.declare_queue(order_created_queue)

    await robust_customer_created_queue.bind(robust_customer_exchange, "customer.customer_created")
    await robust_customer_credit_reservation_queue.bind(robust_customer_exchange, "customer.customer_credit_reservation")
    await robust_customer_credit_limit_exceeded_queue.bind(robust_customer_exchange, "customer.customer_credit_limit_exceeded")

    await robust_order_created_queue.bind(robust_order_exchange, "order.created")



if __name__ == "__main__":
    asyncio.run(app.run())