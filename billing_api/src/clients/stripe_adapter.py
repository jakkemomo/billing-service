"""Module with Stripe client adapter definition"""

from src.core.settings import settings
from src.db.models import Orders
from src.models.common import OrderState, Payment, PaymentMethod, Refund

from .abstract import AbstractClientAdapter
from .stripe.client import StripeClient
from .stripe.utils.converters import (
    convert_charge_status,
    convert_payment_state,
    convert_to_decimal,
    convert_to_int,
)
from .stripe.utils.extractors import get_pmd_extractor

STRIPE_URL = settings.stripe.url
API_KEY = settings.stripe.api_key


class StripeClientAdapter(AbstractClientAdapter):
    """Stripe adapter realization"""

    def __init__(self, client: StripeClient):
        self.client = client

    async def get_payment_status(self, order: Orders, **kwargs) -> OrderState:
        """
        Get Stripe payment status

        @param order: class `Orders` instance with payment data
        @param kwargs: no kwargs is used
        @return: payment status mapped to common order state
        """
        payment = await self.client.get_payment(order.external_id)
        return convert_payment_state(payment)

    async def create_payment(self, order: Orders, **kwargs) -> Payment:
        """
        Get Stripe payment intent

        @param order: class `Orders` instance with payment data
        @param kwargs: no kwargs is used
        @return: created payment data
        """
        customer = await self.client.create_customer(
            str(order.user_id),
            order.user_email,
        )
        stripe_payment = await self.client.create_payment(
            customer.id,
            convert_to_int(order.payment_amount),
            order.payment_currency_code,
            order.user_email,
        )
        return Payment(
            id=stripe_payment.id,
            client_secret=stripe_payment.client_secret,
            is_automatic=stripe_payment.metadata.is_automatic,
            state=convert_payment_state(stripe_payment),
        )

    async def create_recurring_payment(self, order: Orders, **kwargs) -> Payment:
        """
        Create Stripe recurring payment

        @param order: class `Orders` instance with payment data
        @param kwargs: no kwargs is used
        @return: created recurring payment data
        """
        stripe_payment = await self.client.create_recurring_payment(
            str(order.user_id),
            convert_to_int(order.payment_amount),
            order.payment_currency_code,
            order.payment_method.external_id,
        )
        return Payment(
            id=stripe_payment.id,
            is_automatic=stripe_payment.metadata.is_automatic,
            state=convert_payment_state(stripe_payment),
        )

    async def get_refund_status(self, order: Orders, **kwargs) -> OrderState:
        """
        Get Stripe refund status

        @param order: class `Orders` instance with refund data
        @param kwargs: no kwargs is used
        @return: refund status mapped to common order state
        """
        refund = await self.client.get_refund(order.external_id)
        return convert_charge_status(refund.status)

    async def create_refund(self, order: Orders, **kwargs) -> Refund:
        """
        Create Stripe refund

        @param order: class `Orders` instance with refund data
        @param kwargs: no kwargs is used
        @return: created refund data
        """
        refund = await self.client.create_refund(
            order.src_order.external_id,
            convert_to_int(order.payment_amount),
        )
        return Refund(
            id=refund.id,
            amount=convert_to_decimal(refund.amount),
            currency=refund.currency,
            payment_intent_id=refund.payment_intent,
            state=convert_charge_status(refund.status),
        )

    async def get_payment_method(self, order: Orders, **kwargs) -> PaymentMethod:
        """
        Get Stripe customer payment method of specific payment

        @param order: class `Orders` instance with payment data
        @param kwargs: no kwargs is used
        @return: payment method data
        """
        payment = await self.client.get_payment(order.external_id)

        charge = payment.charges.data[0]
        payment_method = charge.payment_method_details

        _id = charge.payment_method
        _type = payment_method["type"]
        pmd_extractor = get_pmd_extractor(_type)
        data = pmd_extractor.extract(payment_method[_type])

        return PaymentMethod(
            id=_id,
            type=_type,
            data=data,
        )

    async def get_payment(self, order: Orders, **kwargs) -> Payment:
        """
        Get Stripe payment data

        @param order: class `Orders` instance with payment data
        @param kwargs: no kwargs is used
        @return: payment data
        """
        stripe_payment = await self.client.get_payment(order.external_id)
        return Payment(
            id=stripe_payment.id,
            client_secret=stripe_payment.client_secret,
            is_automatic=stripe_payment.metadata.is_automatic,
            state=convert_payment_state(stripe_payment),
        )


def get_stripe_adapter() -> AbstractClientAdapter:
    """
    Get configured Stripe client adapter
    @return: Stripe client adapter
    """
    client = StripeClient(STRIPE_URL, API_KEY)
    return StripeClientAdapter(client)
