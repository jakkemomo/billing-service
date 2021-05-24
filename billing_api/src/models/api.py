from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from .common import OrderState, PaymentSystem


class PaymentInfoIn(BaseModel):
    product_id: str
    email: str
    payment_system: PaymentSystem


class PaymentInfoOut(BaseModel):
    payment_system: str
    client_secret: str


class PaymentMethodOut(BaseModel):
    id: UUID
    type: str
    payment_system: PaymentSystem
    is_default: bool
    data: dict


class ProductOut(BaseModel):
    id: UUID
    name: str
    description: str
    price: Decimal
    currency_code: str
    period: int


class SubscriptionOut(BaseModel):
    product: ProductOut
    start_date: date
    end_date: date


class OrderOut(BaseModel):
    product: ProductOut
    payment_system: PaymentSystem
    state: OrderState
    payment_amount: Decimal
    payment_currency_code: str
