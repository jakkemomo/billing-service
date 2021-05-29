from asyncio import get_event_loop_policy

import pytest
from fastapi.testclient import TestClient
from src.clients import stripe_adapter
from src.db.models import Orders, PaymentMethods, Products, Subscriptions
from src.services import auth
from tests.functional.settings import test_settings

from billing_api.src import main
from billing_api.src.main import app, shutdown, startup


@pytest.fixture(scope="session", autouse=True)
async def test_client():
    await mock_api_settings()
    await mock_db_settings()
    client = TestClient(app)
    await startup()
    await setup_db()
    yield client
    await clear_db()
    await shutdown()


async def mock_db_settings():
    main.TORTOISE_CFG = test_settings.TORTOISE_TEST_CFG


async def mock_api_settings():
    stripe_adapter.API_KEY = test_settings.STRIPE_API_KEY
    auth.DEBUG = 1
    auth.DEBUG_USER_ID = test_settings.DEBUG_USER_ID


async def setup_db():
    product = await Products.create(
        name="Basic Subscription",
        description="Sample",
        role_id="2a5ce892-e6a4-439c-93b8-388c96d84f67",
        price=10.0,
        currency_code="usd",
        period=31,
        active=True,
    )
    pytest.product_id = product.id


async def clear_db():
    await Orders.all().delete()
    await Subscriptions.all().delete()
    await Products.all().delete()
    await PaymentMethods.all().delete()


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
