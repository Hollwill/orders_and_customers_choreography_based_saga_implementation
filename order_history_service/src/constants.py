from enum import Enum


class Environment(Enum):
    PRODUCTION = "production"
    LOCAL = "local"


class OrderState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class RejectionReason(Enum):
    INSUFFICIENT_CREDIT = "INSUFFICIENT_CREDIT"
    UNKNOWN_CUSTOMER = "UNKNOWN_CUSTOMER"