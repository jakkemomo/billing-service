import logging
from uuid import uuid4

import backoff
from aiohttp import ClientConnectorError, ClientSession, ServerConnectionError

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

BACKOFF_FACTOR = 1
BACKOFF_BASE = 2
BACKOFF_MAX_VALUE = 30

logger = logging.getLogger(__name__)


class StripeClient:
    URL = "https://api.stripe.com/v1"

    def __init__(self, api_key: str):
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
                handle_response(http_response)
                return http_response

    async def _get(self, entity: str, entity_id: str) -> HTTPResponse:
        method = "GET"
        url = f"{self.URL}/{entity}s/{entity_id}"
        return await self._request(method, url)

    async def _create(self, entity: str, **kwargs) -> HTTPResponse:
        method = "POST"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Idempotency-Key": uuid4(),
        }
        url = f"{self.URL}/{entity}s"
        return await self._request(method, url, data=kwargs, headers=headers)

    async def create_customer(
        self, user_id: str, email: str = None
    ) -> StripeCustomerInner:
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
        resp = await self._get("payment_intent", payment_intent_id)
        return StripePaymentIntent.parse_obj(resp.body)

    async def create_payment(
        self, customer_id: str, amount: int, currency: str
    ) -> StripePaymentIntent:
        metadata = {
            "metadata[is_automatic]": 0,
        }

        payment: StripePaymentIntentInner = StripePaymentIntentInner(
            customer=customer_id,
            amount=amount,
            currency=currency,
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
        resp = await self._get("refund", refund_id)
        return StripeRefund.parse_obj(resp.body)

    async def create_refund(self, payment_intent_id: str, amount: int) -> StripeRefund:
        refund: StripeRefundInner = StripeRefundInner(
            payment_intent=payment_intent_id,
            amount=amount,
        )

        resp = await self._create("refund", **refund.dict())
        return StripeRefund.parse_obj(resp.body)
