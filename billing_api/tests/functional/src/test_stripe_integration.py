import pytest
from src.clients.stripe.client import StripeClient
from src.core.settings import settings
from src.db.models import Orders, Subscriptions
from src.models.common import OrderState, PaymentSystem, SubscriptionState

STRIPE_URL = settings.stripe.url
API_KEY = settings.stripe.api_key
DEBUG_USER_ID = settings.auth.debug_user_id
ACCESS_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkMzA2ZjYyMC0yMDgzLTRjNTUtYjY2Zi03MTcxZmZmZWNjMmIiLCJpYXQiOjE1MTYyMzkwMjJ9.sf4fYKlDrLwtt55dvC_FKy5_MRLnCeUTOCCG723pNIs"


@pytest.mark.asyncio
class TestUser:
    def test_read_docs(self, test_client):
        response = test_client.get("/docs")
        assert response.status_code == 200

    def test_user_payment(self, test_client):
        response = test_client.post(
            "api/user/payment",
            json={
                "email": "spat123@mail.ru",
                "product_id": str(pytest.product_id),
                "payment_system": "stripe",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body.get("payment_system") == "stripe"
        assert body.get("client_secret") is not None

    async def test_order_and_sub_after_user_payment(self):
        order = (
            await Orders.filter(user_id=DEBUG_USER_ID)
            .prefetch_related("subscription", "product")
            .first()
        )
        assert order.state == OrderState.DRAFT
        assert order.product.id == pytest.product_id
        assert order.external_id is not False
        assert order.is_refund is False
        assert order.is_automatic is False
        assert order.payment_amount == 10
        assert order.payment_currency_code == "usd"
        assert order.payment_system == "stripe"
        assert order.user_email == "spat123@mail.ru"
        assert order.subscription.state == SubscriptionState.INACTIVE

    async def test_customer_payment_method(self):
        """
        This functionality is made from User to Stripe directly. Imitate a user inserting a payment method.
        """
        stripe = StripeClient(api_key=API_KEY, url=STRIPE_URL)
        data = {
            "type": "card",
            "card[number]": "4242424242424242",
            "card[exp_month]": 5,
            "card[exp_year]": 2022,
            "card[cvc]": "314",
        }
        response = await stripe._create("payment_method", **data)
        pytest.payment_method_id = response.body["id"]

        response = await stripe._request(
            method="post",
            url=stripe.url + f"/payment_methods/{pytest.payment_method_id}/attach",
            data={"customer": DEBUG_USER_ID},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.body["customer"] == DEBUG_USER_ID
        assert response.body["id"] == pytest.payment_method_id

    async def test_customer_payment_validation(self):
        """ This functionality is made from User to Stripe directly. Imitate confirming a payment intent"""
        stripe = StripeClient(api_key=API_KEY, url=STRIPE_URL)
        order = await Orders.filter(user_id=DEBUG_USER_ID).first()
        pytest.main_order = order.id

        response = await stripe._request(
            method="post",
            url=stripe.url + f"/payment_intents/{order.external_id}/confirm",
            data={"payment_method": pytest.payment_method_id},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status == 200
        assert response.body["status"] == "succeeded"

    def test_update_order_info_method(self, test_client):
        response = test_client.post(
            url=f"api/service/order/{pytest.main_order}/update_info"
        )
        assert response.status_code == 200

    async def test_entities_after_payment_confirmation(self):
        order = await Orders.get_or_none(user_id=DEBUG_USER_ID).prefetch_related(
            "subscription", "payment_method"
        )
        assert order.state == OrderState.PAID

        subscription = order.subscription
        pytest.subscription_id = str(subscription.id)
        assert subscription.state == SubscriptionState.PRE_ACTIVE

        payment_method = order.payment_method
        assert str(payment_method.user_id) == DEBUG_USER_ID
        assert payment_method.external_id == pytest.payment_method_id
        assert payment_method.payment_system == PaymentSystem.STRIPE.value
        assert payment_method.is_default is True
        assert payment_method.data == {
            "brand": "visa",
            "exp_month": 5,
            "exp_year": 2022,
            "last4": "4242",
        }

    def test_subscription_activation(self, test_client):
        response = test_client.post(
            f"/api/service/subscription/{pytest.subscription_id}/activate"
        )
        assert response.status_code == 200

    async def test_subscription_state_after_activation(self):
        sub = await Subscriptions.get_or_none(pk=pytest.subscription_id)
        assert sub.state == SubscriptionState.ACTIVE
        assert str(sub.user_id) == DEBUG_USER_ID

    def test_get_active_subscription(self, test_client):
        response = test_client.get(
            "/api/user/subscription", headers={"Authentication": ACCESS_TOKEN}
        )
        assert response.status_code == 200
        body = response.json()
        assert body.get("product") is not None
        assert body.get("start_date") is not None
        assert body.get("end_date") is not None
        assert body.get("state") == SubscriptionState.ACTIVE.value

    def test_refund_request(self, test_client):
        response = test_client.post(
            "/api/user/subscription/refund", headers={"Authentication": ACCESS_TOKEN}
        )
        assert response.status_code == 200

    async def test_subscription_state_after_refund(self):
        sub = await Subscriptions.get_or_none(pk=pytest.subscription_id)
        assert sub.state == SubscriptionState.TO_DEACTIVATE

    def test_get_active_subscription_after_refund(self, test_client):
        response = test_client.get(
            "/api/user/subscription", headers={"Authentication": ACCESS_TOKEN}
        )
        assert response.status_code == 404
