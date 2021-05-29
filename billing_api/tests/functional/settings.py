from os import environ as env

import jwt
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class TestSettings(BaseSettings):
    STRIPE_API_KEY: str = env.get("STRIPE_API_KEY", "test-api-key")
    DEBUG_USER_ID: str = "d306f620-2083-4c55-b66f-7171fffecc2b"
    ACCESS_TOKEN = str(
        jwt.encode(
            headers={"alg": "HS256", "typ": "JWT"},
            payload={"sub": DEBUG_USER_ID, "iat": 1516239022},
            key="private-sign",
            algorithm="HS256",
        )
    )
    DB_HOST: str = env.get("DB_HOST", "localhost")
    DB_PORT: str = env.get("DB_PORT", "5432")
    DB_USER: str = env.get("DB_USER", "jaqombo")
    DB_PASSWORD: str = env.get("DB_PASSWORD", "12345")
    DB_NAME: str = env.get("DB_NAME", "billing_test")
    DB_SCHEMA: str = env.get("DB_SCHEMA", "data")
    TORTOISE_TEST_CFG: dict = {
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


test_settings = TestSettings()
