from src.clients.abstract import AbstractClientAdapter
from src.clients.stripe_adapter import get_stripe_adapter
from src.models.common import PaymentSystem

_MAPPING = {
    PaymentSystem.STRIPE: get_stripe_adapter,
}


def get_payment_gateway(payment_system: PaymentSystem) -> AbstractClientAdapter:
    client = _MAPPING.get(payment_system, None)
    if not client:
        raise ValueError(
            f"Could not find a client for the payment system '{payment_system}'"
        )
    return client()
