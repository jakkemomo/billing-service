"""Module with Stripe client definition"""

from uuid import uuid4

import backoff
from aiohttp import ClientConnectorError, ClientSession, ServerConnectionError
from src.core.settings import settings

from .exceptions import BadRequest, RequestFailed, TooManyRequests
from .models import (
    HTTPResponse,
    StripeCustomerInner,
    StripePaymentIntent,
    StripePaymentIntentInner,
    StripeRecurringPaymentInner,
    StripeRefund,
    StripeRefundInner,
)
from .utils.exception_handlers import handle_response

BACKOFF_FACTOR = settings.backoff.factor
BACKOFF_BASE = settings.backoff.base
BACKOFF_MAX_VALUE = settings.backoff.max_value


class StripeClient:
    """Class to interact with Stripe API"""

    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key

    @backoff.on_exception(
        backoff.expo,
        (TooManyRequests, ClientConnectorError, ServerConnectionError),
        base=BACKOFF_BASE,
        factor=BACKOFF_FACTOR,
        max_value=BACKOFF_MAX_VALUE,
    )
    async def _request(
        self,
        method: str,
        url: str,
        params: dict = None,
        data: dict = None,
        headers: dict = None,
    ) -> HTTPResponse:
        auth_header = {
            "Authorization": "Bearer %s" % self.api_key,
        }
        async with ClientSession(headers=auth_header) as session:
            async with session.request(
                method, url, params=params, data=data, headers=headers
            ) as resp:
                http_response = HTTPResponse(
                    status=resp.status,
                    body=await resp.json(),
                )
                return handle_response(http_response)

    async def _get(self, entity: str, entity_id: str) -> HTTPResponse:
        method = "GET"
        url = f"{self.url}/{entity}s/{entity_id}"
        return await self._request(method, url)

    async def _create(self, entity: str, **kwargs) -> HTTPResponse:
        method = "POST"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Idempotency-Key": str(uuid4()),
        }
        url = f"{self.url}/{entity}s"
        return await self._request(method, url, data=kwargs, headers=headers)

    async def create_customer(
        self, user_id: str, email: str = None
    ) -> StripeCustomerInner:
        """
        Create a customer

        @param user_id: user identifier in the Stripe payment system
        @param email: user email to send notifications
        @note: user identifier may be specified the same as database identifier for convenience
        @return: class `StripeCustomerInner` if customer is created or already exists
        @raise: exceptions from `exceptions.py` file
        """
        customer: StripeCustomerInner = StripeCustomerInner(
            id=user_id,
            email=email,
        )

        try:
            await self._create("customer", **customer.dict())
        except BadRequest as e:
            if e.response.body["error"]["code"] != "resource_already_exists":
                raise e

        return customer

    async def get_payment(self, payment_intent_id: str) -> StripePaymentIntent:
        """
        Retrieves the details of a PaymentIntent that has previously been created

        @param payment_intent_id: payment intent identifier in the Stripe payment system
        @return: class `StripePaymentIntent` instance
        @raise: exceptions from `exceptions.py` file
        """
        resp = await self._get("payment_intent", payment_intent_id)
        return StripePaymentIntent.parse_obj(resp.body)

    async def create_payment(
        self, customer_id: str, amount: int, currency: str, email: str
    ) -> StripePaymentIntent:
        """
        Creates a PaymentIntent object

        @param customer_id: ID of the Customer this PaymentIntent belongs to, if one exists
        @param amount: Amount intended to be collected by this PaymentIntent
        @param currency: Three-letter ISO currency code, in lowercase
        @param email: Customer email to send notifications
        @return: class `StripePaymentIntent` instance
        @raise: exceptions from `exceptions.py` file
        """
        metadata = {
            "metadata[is_automatic]": 0,
        }

        payment: StripePaymentIntentInner = StripePaymentIntentInner(
            customer=customer_id,
            amount=amount,
            currency=currency,
            receipt_email=email,
        )

        data = {**payment.dict(), **metadata}
        resp = await self._create("payment_intent", **data)
        return StripePaymentIntent.parse_obj(resp.body)

    async def create_recurring_payment(
        self,
        customer_id: str,
        amount: int,
        currency: str,
        payment_method_id: str,
    ) -> StripePaymentIntent:
        """
         Create recurring payment intent

        @param customer_id: ID of the Customer this PaymentIntent belongs to, if one exists
        @param amount: Amount intended to be collected by this PaymentIntent
        @param currency: Three-letter ISO currency code, in lowercase
        @param payment_method_id: ID of the payment method to attach to this PaymentIntent
        @return: class `StripePaymentIntent` instance
        @raise: exceptions from `exceptions.py` file
        """
        metadata = {
            "metadata[is_automatic]": 1,
        }

        payment: StripeRecurringPaymentInner = StripeRecurringPaymentInner(
            customer=customer_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method_id,
        )

        data = {**payment.dict(), **metadata}

        try:
            resp = await self._create("payment_intent", **data)
        except RequestFailed as e:
            payment_data = e.response.body["error"]["payment_intent"]
        else:
            payment_data = resp.body

        return StripePaymentIntent.parse_obj(payment_data)

    async def get_refund(self, refund_id: str) -> StripeRefund:
        """
        Retrieve a refund information

        @param refund_id: refund identifier
        @return: class `StripeRefund` instance if a valid ID was provided, raise an exception otherwise
        @raise: exceptions from `exceptions.py` file
        """
        resp = await self._get("refund", refund_id)
        return StripeRefund.parse_obj(resp.body)

    async def create_refund(self, payment_intent_id: str, amount: int) -> StripeRefund:
        """
        Create a refund

        @param payment_intent_id: ID of the PaymentIntent to refund
        @param amount: a positive integer in cents representing how much of this charge to refund,
        can refund only up to the remaining, unrefunded amount of the charge
        @return: class `StripeRefund` instance if the refund succeeded, raise an exception if the PaymentIntent
        has already been refunded, or if an invalid identifier was provided
        @raise: exceptions from `exceptions.py` file
        """
        refund: StripeRefundInner = StripeRefundInner(
            payment_intent=payment_intent_id,
            amount=amount,
        )

        resp = await self._create("refund", **refund.dict())
        return StripeRefund.parse_obj(resp.body)
