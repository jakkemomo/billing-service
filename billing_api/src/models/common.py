from enum import Enum


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
