from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class StripePaymentStatus(str, Enum):
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTIONS = "requires_action"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


class StripeChargeStatus(str, Enum):
    SUCCEEDED = "succeeded"
    PENDING = "pending"
    FAILED = "failed"


@dataclass
class HTTPResponse:
    status: int
    body: dict


class StripeCustomer(BaseModel):
    id: str
    email: Optional[str]


class StripePayment(BaseModel):
    customer: str
    amount: int
    currency: str
    setup_future_usage: str = "off_session"


class StripeRecurringPayment(BaseModel):
    customer: str
    amount: int
    currency: str
    payment_method: str
    off_session: bool = True
    confirm: bool = True


class StripeRefund(BaseModel):
    payment_intent: str
    amount: int
