
import pytest
from sqlalchemy import select

from src.models import Order
from src.schemas import OrderCreateSchema


@pytest.mark.asyncio
async def test_create_order(db_session, order_service):
    order = await order_service.create_order(OrderCreateSchema(customer_id=1, order_total=100))

    order = (await db_session.execute(select(Order).where(Order.id == order.id))).scalar_one_or_none()

    assert order
    assert order.customer_id == 1
    assert order.order_total == 100
    assert order.deleted_at is None
