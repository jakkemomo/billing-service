from typing import Optional

from pydantic import BaseModel
from src.models.common import OrderState


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
