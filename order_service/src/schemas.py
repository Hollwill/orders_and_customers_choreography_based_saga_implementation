
from pydantic import BaseModel

from src.constants import OrderState, RejectionReason


class OrderSchema(BaseModel):
    id: int
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
