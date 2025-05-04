
from pydantic import BaseModel, Field

from src.constants import OrderState, RejectionReason


class OrderSchema(BaseModel):
    id: int = Field(alias="_id")
    state: OrderState
    rejection_reason: RejectionReason | None

class OrderCreateSchema(BaseModel):
    customer_id: int
    order_total: int

class OrderHandledConsumerSchema(BaseModel):
    aggregate_id: int
    order_id: int

class CustomerNotFoundConsumerSchema(OrderHandledConsumerSchema):
    pass

class CustomerCreditReservationConsumerSchema(OrderHandledConsumerSchema):
    pass

class CustomerCreditLimitExceededConsumerSchema(OrderHandledConsumerSchema):
    pass

class CustomerOrderHistorySchema(BaseModel):
    id: int = Field(alias="_id")
    orders: list[OrderSchema]
    name: str
    money_limit: int

class CustomerCreatedSchema(BaseModel):
    aggregate_id: int
    name: str
    money_limit: int

class CreditReservationSchema(BaseModel):
    aggregate_id: int
    order_id: int

class CreditLimitExceededSchema(BaseModel):
    aggregate_id: int
    order_id: int

class OrderCreatedSchema(BaseModel):
    aggregate_id: int
    customer_id: int
    order_total: int
