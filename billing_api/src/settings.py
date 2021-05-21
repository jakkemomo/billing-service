import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
TORTOISE_CFG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "billing_db",
                "port": "5432",
                "user": "jaqombo",
                "password": "12345",
                "database": "billing",
                "schema": "data",
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
