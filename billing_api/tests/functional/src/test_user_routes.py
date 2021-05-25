import pytest
from src.clients.stripe.client import StripeClient
from src.core.settings import settings
from src.db.models import Orders

stripe_url = settings.stripe.url
API_KEY = settings.stripe.api_key
DEBUG_USER_ID = settings.auth.debug_user_id


@pytest.mark.asyncio
class TestUser:
    def test_read_docs(self, test_client):
        response = test_client.get("/docs")
        assert response.status_code == 200

    def test_make_user_payment(self, test_client):
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

    async def test_create_customer_payment_method(self):
        """
        This functionality is made from User to Stripe directly. Imitate a user inserting a payment method.
        """
        stripe = StripeClient(api_key=API_KEY, url=stripe_url)
        data = {
            "type": "card",
            "card[number]": "4242424242424242",
            "card[exp_month]": 5,
            "card[exp_year]": 2022,
            "card[cvc]": "314",
        }
        response = await stripe._create("payment_method", **data)
        pytest.payment_method_id = response.body["id"]
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = await stripe._request(
            "post",
            stripe.url + f"/payment_methods/{pytest.payment_method_id}/attach",
            data={"customer": DEBUG_USER_ID},
            headers=headers,
        )
        assert response.body["customer"] == DEBUG_USER_ID
        assert response.body["id"] == pytest.payment_method_id

    # проверить, что создался ордер, подписка и что ордер обновился с external_id
    async def test_customer_payment_validation(self):
        """ This functionality is made from User to Stripe directly. Imitate confirming a payment intent"""
        stripe = StripeClient(api_key=API_KEY, url=stripe_url)
        order = await Orders.filter(user_id=DEBUG_USER_ID).first()
        pytest.main_order = order.id
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = await stripe._request(
            method="post",
            url=stripe.url + f"/payment_intents/{order.external_id}/confirm",
            data={"payment_method": pytest.payment_method_id},
            headers=headers,
        )
        assert response.status == 200
        assert response.body["status"] == "succeeded"

    def test_order_state_after_payment(self, test_client):
        response = test_client.post(
            f"api/service/order/{pytest.main_order}/update_info"
        )
        assert response.status_code == 200

        # проверить статус подписки = pre_active
        # проверить созданный payment_method в бд

    # тест рефандов
