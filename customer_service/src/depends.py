from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

from src.database import get_engine
from src.services import OutboxSaveService, CustomerService


async def get_session(engine: AsyncEngine =  Depends(get_engine)) -> AsyncGenerator[AsyncSession, None]:
    db = AsyncSession(
        bind=engine,
    )
    try:
        yield db
    finally:
        await db.close()

async def get_outbox_save_service(session: AsyncSession = Depends(get_session)) -> OutboxSaveService:
    return OutboxSaveService(session)

async def get_customer_service(session: AsyncSession = Depends(get_session), outbox_save_service: OutboxSaveService = Depends(get_outbox_save_service)) -> CustomerService:
    return CustomerService(session, outbox_save_service)
