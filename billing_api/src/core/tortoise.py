"""Module with tortoise configuration options"""

from .settings import settings

TORTOISE_CFG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": settings.db.dict(by_alias=True),
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
