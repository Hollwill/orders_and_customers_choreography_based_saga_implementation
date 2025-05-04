from decimal import Decimal
from typing import Any, Coroutine, Sequence

from fastapi import FastAPI, Depends
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.depends import get_session, get_customer_service
from src.models import Customer
from src.schemas import CustomerShortSchema, CustomerSchema, CustomerCreateSchema
from src.services import CustomerService

app = FastAPI()



@app.get("/customers")
async def get_customers_list(session: AsyncSession = Depends(get_session)) -> Sequence[CustomerShortSchema]:
    async with session.begin():
        result = await session.execute(select(Customer).where(Customer.deleted_at.is_(None)))
        return TypeAdapter(list[CustomerShortSchema]).validate_python(result.scalars().all(), from_attributes=True)

@app.get("/customers/{item_id}")
async def get_customer(item_id: int, session: AsyncSession = Depends(get_session)) -> CustomerSchema:
    async with session.begin():
        result = await session.execute(select(Customer).where(Customer.id == item_id, Customer.deleted_at.is_(None)))
        return CustomerSchema.model_validate(result.scalar_one(), from_attributes=True)

@app.post("/customers")
async def create_customer(customer_in: CustomerCreateSchema, session: AsyncSession = Depends(get_session), customer_service: CustomerService = Depends(get_customer_service)) -> CustomerShortSchema:
    async with session.begin():
        customer = await customer_service.create_customer(customer_in)
        return CustomerShortSchema.model_validate(customer, from_attributes=True)
