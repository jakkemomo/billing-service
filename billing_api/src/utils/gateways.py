from src.adapters.abstract import AbstractAdapter
from src.adapters.stripe import get_stripe_adapter


def get_payment_gateway(payment_system: str) -> AbstractAdapter:
    if payment_system == "stripe":
        return get_stripe_adapter()
    else:
        raise ValueError(f"Could not find a payment system  with name '{payment_system}'")
