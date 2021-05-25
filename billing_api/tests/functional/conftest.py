from asyncio import get_event_loop_policy
from os import environ as env

import pytest
from billing_api.src import main
from billing_api.src.main import app, shutdown, startup
from billing_api.src.services import auth
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from src.db.models import Orders, PaymentMethods, Products, Subscriptions

load_dotenv()

DB_HOST: str = env.get("DB_HOST", "localhost")
DB_PORT: str = env.get("DB_PORT", "5432")
DB_USER: str = env.get("DB_USER", "jaqombo")
DB_PASSWORD: str = env.get("DB_PASSWORD", "12345")
DB_NAME: str = env.get("DB_NAME", "billing_test")
DB_SCHEMA: str = env.get("DB_SCHEMA", "data")

TORTOISE_TEST_CFG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": DB_HOST,
                "port": DB_PORT,
                "user": DB_USER,
                "password": DB_PASSWORD,
                "database": DB_NAME,
                "schema": DB_SCHEMA,
            },
        },
    },
    "apps": {
        "billing": {
            "models": ["src.db.models"],
        }
    },
    "use_tz": True,
    "timezone": "W-SU",
}


@pytest.fixture(scope="session", autouse=True)
async def test_client(event_loop):
    await mock_db_settings()
    client = TestClient(app)
    await startup()
    await setup_db()
    yield client
    await clear_db()
    await shutdown()


async def mock_db_settings():
    auth.debug_user_id = "d306f620-2083-4c55-b66f-7171fffecc2b"
    auth.auth_debug = 1
    main.TORTOISE_CFG = TORTOISE_TEST_CFG


async def setup_db():
    product = await Products.create(
        name="Basic Subscription",
        description="Sample",
        role_id="48c400a4-1654-45e3-a039-5b7afc709128",
        price=10.0,
        currency_code="usd",
        period=30,
        active=True,
    )
    pytest.product_id = product.id


async def clear_db():
    await Orders.all().delete()
    await Subscriptions.all().delete()
    await Products.all().delete()
    await PaymentMethods.all().delete()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
