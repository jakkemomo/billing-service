from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SubscriptionState(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"


class OrderState(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    PAID = "paid"
    ERROR = "error"


class PaymentSystem(str, Enum):
    STRIPE = "stripe"


class PaymentMethod(BaseModel):
    id: str
    type: str
    data: dict


class Payment(BaseModel):
    id: str
    client_secret: Optional[str]
    state: OrderState
    is_automatic: bool


class Refund(BaseModel):
    id: str
    amount: int
    currency: str
    payment_intent_id: str
    state: OrderState
