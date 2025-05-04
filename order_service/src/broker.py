from faststream.rabbit import RabbitBroker, RabbitExchange

from src.config import settings
from src.events import OrderCreatedEvent

events = [
    OrderCreatedEvent,
]


def get_broker() -> RabbitBroker:
    return RabbitBroker(settings.RABBITMQ_URL)


async def declare_exchanges(broker: RabbitBroker):
    exchanges = []
    for event in events:
        if event.exchange not in exchanges:
            exchanges.append(event.exchange)

    for exchange in exchanges:
        await broker.declare_exchange(RabbitExchange(exchange))