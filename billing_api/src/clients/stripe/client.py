from aiohttp import ClientSession
from src.clients.abstract import AbstractClient
from src.clients.models import Payment, PaymentMethod, Refund
from src.models.common import OrderState
from src.orm.models import Orders
from src.settings import STRIPE_API_KEY

from .exceptions import (
    ArgumentValueError,
    BadRequest,
    RequestConflict,
    RequestFailed,
    ResourceNotFound,
    StripeInternalError,
    TooManyRequests,
)
from .models import (
    HTTPResponse,
    StripeChargeStatus,
    StripeCustomer,
    StripePayment,
    StripeRecurringPayment,
    StripeRefund,
)
from .utils import extract_payment_state, get_pmd_extractor, map_refund_status

API_KEY = STRIPE_API_KEY


class StripeClient(AbstractClient):
    URL = "https://api.stripe.com/v1/"

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
        url = "%s%ss/%s" % (self.URL, entity, entity_id)
        return await self._request(method, url)

    async def _create(self, entity: str, **kwargs) -> HTTPResponse:
        method = "POST"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        url = "%s%ss" % (self.URL, entity)
        return await self._request(method, url, data=kwargs, headers=headers)

    async def create_customer(self, user_id: str, email: str = None) -> StripeCustomer:
        customer: StripeCustomer = StripeCustomer(
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

    async def get_payment_status(self, order: Orders, **kwargs) -> OrderState:
        payment_intent_id = order.external_id
        if not payment_intent_id:
            raise ArgumentValueError("`Order.external_id` must have not `None` value")

        resp = await self._get("payment_intent", payment_intent_id)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        if resp.status == 404:
            raise ResourceNotFound()

        return extract_payment_state(resp.body)

    async def get_payment(self, order: Orders, **kwargs) -> Payment:
        resp = await self._get("payment_intent", order.external_id)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        if resp.status == 404:
            raise ResourceNotFound()

        return Payment(
            id=resp.body["id"],
            client_secret=resp.body["client_secret"],
            is_automatic=bool(int(resp.body["metadata"]["is_automatic"])),
            state=extract_payment_state(resp.body),
        )

    async def create_payment(self, order: Orders, **kwargs) -> Payment:
        customer = await self.create_customer(str(order.user_id), order.user_email)

        metadata = {
            "metadata[is_automatic]": 0,
        }

        payment: StripePayment = StripePayment(
            customer=customer.id,
            amount=self._convert_price(order.payment_amount),
            currency=order.payment_currency_code,
        )

        data = {**payment.dict(), **metadata}

        resp = await self._create("payment_intent", **data)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        return Payment(
            id=resp.body["id"],
            client_secret=resp.body["client_secret"],
            is_automatic=False,
            state=extract_payment_state(resp.body),
        )

    async def create_recurring_payment(self, order: Orders, **kwargs) -> Payment:
        metadata = {
            "metadata[is_automatic]": 1,
        }

        payment: StripeRecurringPayment = StripeRecurringPayment(
            customer=str(order.user_id),
            amount=self._convert_price(order.payment_amount),
            currency=order.payment_currency_code,
            payment_method=order.payment_method.external_id,
        )

        data = {**payment.dict(), **metadata}

        resp = await self._create("payment_intent", **data)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            resp.body = resp.body["error"]["payment_intent"]

        return Payment(
            id=resp.body["id"],
            is_automatic=True,
            state=extract_payment_state(resp.body),
        )

    async def get_refund_status(self, order: Orders, **kwargs) -> OrderState:
        resp = await self._get("refund", order.external_id)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        if resp.status == 404:
            raise ResourceNotFound()

        return map_refund_status(StripeChargeStatus(resp.body["status"]))

    async def create_refund(self, order: Orders, **kwargs) -> Refund:
        refund: StripeRefund = StripeRefund(
            payment_intent=order.src_order.external_id,
            amount=self._convert_price(order.payment_amount),
        )

        resp = await self._create("refund", **refund.dict())

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        return Refund(
            id=resp.body["id"],
            amount=resp.body["amount"],
            currency=resp.body["currency"],
            payment_intent_id=resp.body["payment_intent"],
            state=map_refund_status(StripeChargeStatus(resp.body["status"])),
        )

    async def get_payment_method(self, order: Orders, **kwargs) -> PaymentMethod:
        resp = await self._get("payment_intent", order.external_id)

        if resp.status == 400:
            raise BadRequest()

        if resp.status == 402:
            raise RequestFailed()

        if resp.status == 404:
            raise ResourceNotFound()

        charge = resp.body["charges"]["data"][0]
        payment_method = charge["payment_method_details"]

        _id = charge["payment_method"]
        _type = payment_method["type"]
        pmd_extractor = get_pmd_extractor(_type)
        data = pmd_extractor.extract(payment_method[_type])

        return PaymentMethod(
            id=_id,
            type=_type,
            data=data,
        )

    @staticmethod
    def _convert_price(price: float):
        return price * 100


def get_stripe_client() -> StripeClient:
    return StripeClient(API_KEY)
