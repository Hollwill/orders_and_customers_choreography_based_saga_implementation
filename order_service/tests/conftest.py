import asyncio
from typing import AsyncGenerator

import pytest

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

from src.config import settings
from src.models import Base
from src.services import OrderService, OutboxSaveService


@pytest.fixture(scope='session', autouse=True)
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def db_engine():
    admin_engine = create_async_engine(settings.DATABASE_URL.unicode_string())
    async with admin_engine.connect() as conn:
        await conn.execute(text("COMMIT"))
        test_db_name = f"order_service_test"
        await conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        await conn.execute(text(f"CREATE DATABASE {test_db_name}"))

    test_engine = create_async_engine(settings.TEST_DATABASE_URL.unicode_string())

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield test_engine
    finally:

        await test_engine.dispose()
        async with admin_engine.connect() as conn:
            await conn.execute(text("COMMIT"))
            await conn.execute(text(f"DROP DATABASE IF EXISTS  {test_db_name} WITH (FORCE)"))
        await admin_engine.dispose()


@pytest_asyncio.fixture(loop_scope="session", scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSession(bind=db_engine)

    try:
        await session.begin()
        yield session
    finally:
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(loop_scope="session", scope="function")
async def order_service(db_session) -> AsyncGenerator[OrderService, None]:

    events_save_service = OutboxSaveService(db_session)

    service = OrderService(db_session, events_save_service)
    yield service