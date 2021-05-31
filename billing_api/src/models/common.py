"""Module with common models"""

from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SubscriptionState(str, Enum):
    """Subscription states enum"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PRE_ACTIVE = "pre_active"
    TO_DEACTIVATE = "to_deactivate"


class OrderState(str, Enum):
    """Order states enum"""

    DRAFT = "draft"
    PROCESSING = "processing"
    PAID = "paid"
    ERROR = "error"


class PaymentSystem(str, Enum):
    """Payment systems enum"""

    STRIPE = "stripe"


class PaymentMethod(BaseModel):
    """Payment method model"""

    id: str
    type: str
    data: dict


class Payment(BaseModel):
    """Payment model"""

    id: str
    client_secret: Optional[str]
    state: OrderState
    is_automatic: bool


class Refund(BaseModel):
    """Refund model"""

    id: str
    amount: Decimal
    currency: str
    payment_intent_id: str
    state: OrderState
