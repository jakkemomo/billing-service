import logging
from os import environ as env

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
DB_HOST: str = env.get("DB_HOST", "billing_db")
DB_PORT: str = env.get("DB_PORT", "5432")
DB_USER: str = env.get("DB_USER", "jaqombo")
DB_PASSWORD: str = env.get("DB_PASSWORD", "12345")
DB_NAME: str = env.get("DB_NAME", "billing")
DB_SCHEMA: str = env.get("DB_SCHEMA", "data")
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
            "models": ["orm.models", "aerich.models"],
        }
    },
    "use_tz": True,
    "timezone": "W-SU",
}
