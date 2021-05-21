from uuid import UUID

from pydantic import BaseModel

from .common import PaymentSystem


class PaymentInfoIn(BaseModel):
    product_id: str
    email: str
    payment_system: PaymentSystem


class PaymentInfoOut(BaseModel):
    payment_system: str
    client_secret: str
    is_new: bool


class PaymentMethodOut(BaseModel):
    id: UUID
    type: str
    payment_system: str
    is_default: bool
    data: dict


class ProductOut(BaseModel):
    name: str
    description: str
    price: str
    currency_code: str
    period: str


class SubscriptionOut(BaseModel):
    product_name: str
    start_date: str
    end_date: str
