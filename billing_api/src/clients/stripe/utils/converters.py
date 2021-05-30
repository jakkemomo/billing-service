"""Module with converters from Stripe to common categories"""

from decimal import Decimal

from src.clients.stripe.models import StripePaymentIntent
from src.clients.stripe.models import StripePaymentStatus, StripeChargeStatus
from src.models.common import OrderState


def convert_payment_state(payment_intent: StripePaymentIntent) -> OrderState:
    """
    Map Stripe payment intent state to common order state

    @param payment_intent: details of a PaymentIntent
    @return: class `OrderState` instance
    """
    is_automatic = payment_intent.metadata.is_automatic
    pi_status = payment_intent.status
    charges = payment_intent.charges.data
    charge = charges[0] if charges else None
    charge_status = charge.status if charge else None
    charge_status_mapping = {
        StripeChargeStatus.FAILED: OrderState.ERROR,
        StripeChargeStatus.PENDING: OrderState.PROCESSING
    }
    pi_status_mapping = {
        StripePaymentStatus.SUCCEEDED: OrderState.PAID,
        StripePaymentStatus.PROCESSING: OrderState.PROCESSING,
        StripePaymentStatus.REQUIRES_ACTIONS: OrderState.DRAFT,
    }
    order_state = pi_status_mapping.get(pi_status)
    if order_state:
        return order_state

    if is_automatic:
        if pi_status == StripePaymentStatus.REQUIRES_PAYMENT_METHOD:
            status = charge_status_mapping.get(charge_status)
            if status:
                return status
    else:
        if pi_status == StripePaymentStatus.REQUIRES_PAYMENT_METHOD:
            if charge:
                status = charge_status_mapping.get(charge_status)
                if status:
                    return status
            else:
                return OrderState.DRAFT
        return OrderState.PROCESSING


def convert_charge_status(status: StripeChargeStatus) -> OrderState:
    """
    Map Stripe charge status to common order state

    @param status: Stripe charge status
    @return: common order state
    """
    mapping = {
        StripeChargeStatus.FAILED: OrderState.ERROR,
        StripeChargeStatus.PENDING: OrderState.PROCESSING,
        StripeChargeStatus.SUCCEEDED: OrderState.PAID,
    }
    return mapping[status]


def convert_to_int(price: Decimal) -> int:
    """
    Convert price from base to minor currency unit

    @param price: price in base currency unit
    @return: price in minor currency unit
    """
    return int(price * 100)


def convert_to_decimal(price: int) -> Decimal:
    """
    Convert price from minor to base currency unit

    @param price: price in minor currency unit
    @return: price in base currency unit
    """
    return Decimal(price / 100)
