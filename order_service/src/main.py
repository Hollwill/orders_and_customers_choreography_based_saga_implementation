from typing import Sequence

from fastapi import FastAPI, Depends, HTTPException
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.depends import get_session, get_order_service
from src.models import Order
from src.schemas import OrderSchema, OrderCreateSchema
from src.services import OrderService

app = FastAPI()


@app.get("/orders")
async def get_orders_list(session: AsyncSession = Depends(get_session)) -> Sequence[OrderSchema]:
    async with session.begin():
        result = await session.execute(select(Order).where(Order.deleted_at.is_(None)))
        return TypeAdapter(list[OrderSchema]).validate_python(result.scalars().all(), from_attributes=True)


@app.get("/orders/{item_id}")
async def get_order(item_id: int, session: AsyncSession = Depends(get_session), order_service: OrderService = Depends(get_order_service)) -> OrderSchema:
    async with session.begin():
        order = await order_service.get_order_by_id(item_id)

        return OrderSchema.model_validate(order, from_attributes=True)


@app.post("/orders")
async def create_order(order_in: OrderCreateSchema, session: AsyncSession = Depends(get_session), order_service: OrderService = Depends(get_order_service) ) -> OrderSchema:
    async with session.begin():
        result = await order_service.create_order(order_in)
        return OrderSchema.model_validate(result, from_attributes=True)


@app.post("/orders/{item_id}/cancel/", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(order_id: int, session: AsyncSession = Depends(get_session), order_service: OrderService = Depends(get_order_service)):
    async with session.begin():
        await order_service.cancel_order(order_id)

