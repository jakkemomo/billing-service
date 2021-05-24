import logging
from os import environ as env

from core.logging import LOGGING_CFG
from dotenv import load_dotenv

load_dotenv()

logging.config.dictConfig(LOGGING_CFG)

DB_HOST: str = env.get("DB_HOST", "localhost")
DB_PORT: str = env.get("DB_PORT", "5432")
DB_USER: str = env.get("DB_USER", "billingapi")
DB_PASSWORD: str = env.get("DB_PASSWORD", "billingapi")
DB_NAME: str = env.get("DB_NAME", "billing")
DB_SCHEMA: str = env.get("DB_SCHEMA", "content")
STRIPE_API_KEY = "sk_test_51InhtFIopSoE9boMy4b9JNDwgInO7S5xDpqsW1A1kL3SixGsw5EcGBG75TqpG3uTUDrpuA5OEPpXJeJBXTSlkO6d00WUws4eqc"

TORTOISE_CFG = {
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
            "models": ["src.orm.models", "aerich.models"],
        }
    },
    "use_tz": True,
    "timezone": "W-SU",
}
