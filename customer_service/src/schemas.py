from pydantic import BaseModel
from sqlalchemy.orm import Mapped


class CustomerShortSchema(BaseModel):
    id: int
    name: str
    money_limit: float

class CreditReservationSchema(BaseModel):
    amount: float


class CustomerSchema(CustomerShortSchema):
    credit_reservations: list[CreditReservationSchema]

class CustomerCreateSchema(BaseModel):
    name: str
    money_limit: int


class OrderCreatedSchema(BaseModel):
    aggregate_id: int
    customer_id: int
    order_total: int

class OrderCanceledSchema(BaseModel):
    aggregate_id: int
    customer_id: int