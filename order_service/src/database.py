from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession

from src.config import settings


def get_engine() -> AsyncEngine:
    return create_async_engine(settings.DATABASE_URL.unicode_string(), echo=settings.DATABASE_ECHO)


@asynccontextmanager
async def async_context_get_session() -> AsyncGenerator:
    session = AsyncSession(
        bind=get_engine(),
    )
    try:
        await session.begin()
        yield session
    finally:
        await session.commit()
        await session.close()
