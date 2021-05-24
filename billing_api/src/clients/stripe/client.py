from aiohttp import ClientSession

from .exceptions import (
    BadRequest,
    RequestConflict,
    RequestFailed,
    ResourceNotFound,
    StripeInternalError,
    TooManyRequests,
)
from .models import (
    HTTPResponse,
    StripeCustomerInner,
    StripePaymentIntent,
    StripePaymentIntentInner,
    StripeRecurringPaymentInner,
    StripeRefund,
    StripeRefundInner,
)


class StripeClient:
    URL = "https://api.stripe.com/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

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

                if http_response.status == 429:
                    raise TooManyRequests()

                if http_response.status == 409:
                    raise RequestConflict()

                if http_response.status in [500, 502, 503, 504]:
                    raise StripeInternalError()

                return http_response

    async def _get(self, entity: str, entity_id: str) -> HTTPResponse:
        method = "GET"
        url = f"{self.URL}/{entity}s/{entity_id}"
        return await self._request(method, url)

    async def _create(self, entity: str, **kwargs) -> HTTPResponse:
        method = "POST"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        url = f"{self.URL}/{entity}s"
        return await self._request(method, url, data=kwargs, headers=headers)

    async def create_customer(
        self, user_id: str, email: str = None
    ) -> StripeCustomerInner:
        customer: StripeCustomerInner = StripeCustomerInner(
            id=user_id,
            email=email,
        )

        resp = await self._create("customer", **customer.dict())

        if resp.status == 400:
            if resp.body["error"]["code"] == "resource_already_exists":
                return customer
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        return customer

    async def get_payment(self, payment_intent_id: str) -> StripePaymentIntent:
        resp = await self._get("payment_intent", payment_intent_id)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        if resp.status == 404:
            raise ResourceNotFound()

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

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

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

        resp = await self._create("payment_intent", **data)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            resp.body = resp.body["error"]["payment_intent"]

        return StripePaymentIntent.parse_obj(resp.body)

    async def get_refund(self, refund_id: str) -> StripeRefund:
        resp = await self._get("refund", refund_id)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        if resp.status == 404:
            raise ResourceNotFound()

        return StripeRefund.parse_obj(resp.body)

    async def create_refund(self, payment_intent_id: str, amount: int) -> StripeRefund:
        refund: StripeRefundInner = StripeRefundInner(
            payment_intent=payment_intent_id,
            amount=amount,
        )

        resp = await self._create("refund", **refund.dict())

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        return StripeRefund.parse_obj(resp.body)
