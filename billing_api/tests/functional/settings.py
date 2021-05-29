import os

import jwt
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class TestSettings(BaseSettings):
    STRIPE_API_KEY: str = os.environ.get("STRIPE_API_KEY", "test-api-key")
    DEBUG_USER_ID: str = "d306f620-2083-4c55-b66f-7171fffecc2b"
    ACCESS_TOKEN = jwt.encode(
        headers={"alg": "HS256", "typ": "JWT"},
        payload={"sub": DEBUG_USER_ID, "iat": 1516239022},
        key="private-sign",
        algorithm="HS256",
    )


test_settings = TestSettings()
