from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from src.config import settings


async def get_database() -> AsyncDatabase:
    client = AsyncMongoClient(settings.DATABASE_URL.unicode_string())
    db = client.orders_history_service
    return db

async def get_order_history_collection() -> AsyncCollection:
    db = await get_database()
    return db.order_history_collection
