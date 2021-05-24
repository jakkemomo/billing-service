from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

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


class StripeCustomerInner(BaseModel):
    id: str
    email: Optional[str]


class StripePaymentIntentInner(BaseModel):
    customer: str
    amount: int
    currency: str
    setup_future_usage: str = "off_session"


class StripeRecurringPaymentInner(BaseModel):
    customer: str
    amount: int
    currency: str
    payment_method: str
    off_session: bool = True
    confirm: bool = True


class StripeRefundInner(BaseModel):
    payment_intent: str
    amount: int


class Charge(BaseModel):
    id: str
    payment_method: str
    payment_method_details: dict
    status: StripeChargeStatus


class Charges(BaseModel):
    data: List[Charge]


class Metadata(BaseModel):
    is_automatic: bool


class StripePaymentIntent(BaseModel):
    id: str
    client_secret: Optional[str]
    status: StripePaymentStatus
    charges: Charges
    metadata: Metadata


class StripeRefund(BaseModel):
    id: str
    amount: int
    currency: str
    reason: Optional[str]
    payment_intent: str
    status: StripeChargeStatus
