import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.broker import get_broker, declare_exchanges
from src.database import async_context_get_session
from src.services import OutboxPublishService

async def publish_outbox_messages():
    async with async_context_get_session() as session:

        broker = get_broker()
        await broker.connect()
        await declare_exchanges(broker)

        service = OutboxPublishService(session, broker)
        await service.publish_all()

        await broker.close()
        await session.commit()


async def main():
    scheduler = AsyncIOScheduler()

    scheduler.add_job(publish_outbox_messages, trigger="interval", seconds=5)

    scheduler.start()

    while True:
        await asyncio.sleep(1000)


if __name__ == "__main__":
    asyncio.run(main())