from src.models.common import OrderState, Payment, PaymentMethod, Refund
from src.orm.models import Orders

from .abstract import AbstractClientAdapter
from .stripe.client import StripeClient
from .stripe.utils.converters import (
    convert_payment_state,
    convert_refund_status,
    convert_to_decimal,
    convert_to_int,
)
from .stripe.utils.extractors import get_pmd_extractor

API_KEY = "sk_test_51Imm7vKDxYta8liOnRXex80p2LNsuFbTimUwRI1x4I72EEuqw2xQjUyEpyd1yhnprGL8cYY1bYt6ZInMP0MBY2TG00F4HWdvIa"


class StripeClientAdapter(AbstractClientAdapter):
    def __init__(self, client: StripeClient):
        self.client = client

    async def get_payment_status(self, order: Orders, **kwargs) -> OrderState:
        payment = await self.client.get_payment(order.external_id)
        return convert_payment_state(payment)

    async def create_payment(self, order: Orders, **kwargs) -> Payment:
        customer = await self.client.create_customer(
            str(order.user_id),
            order.user_email,
        )
        stripe_payment = await self.client.create_payment(
            customer.id,
            convert_to_int(order.payment_amount),
            order.payment_currency_code,
        )
        return Payment(
            id=stripe_payment.id,
            client_secret=stripe_payment.client_secret,
            is_automatic=stripe_payment.metadata.is_automatic,
            state=convert_payment_state(stripe_payment),
        )

    async def create_recurring_payment(self, order: Orders, **kwargs) -> Payment:
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
        refund = await self.client.get_refund(order.external_id)
        return convert_refund_status(refund.status)

    async def create_refund(self, order: Orders, **kwargs) -> Refund:
        refund = await self.client.create_refund(
            order.src_order.external_id,
            convert_to_int(order.payment_amount),
        )
        return Refund(
            id=refund.id,
            amount=convert_to_decimal(refund.amount),
            currency=refund.currency,
            payment_intent_id=refund.payment_intent,
            state=convert_refund_status(refund.status),
        )

    async def get_payment_method(self, order: Orders, **kwargs) -> PaymentMethod:
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
        stripe_payment = await self.client.get_payment(order.external_id)
        return Payment(
            id=stripe_payment.id,
            client_secret=stripe_payment.client_secret,
            is_automatic=stripe_payment.metadata.is_automatic,
            state=convert_payment_state(stripe_payment),
        )


def get_stripe_adapter() -> AbstractClientAdapter:
    client = StripeClient(API_KEY)
    return StripeClientAdapter(client)
