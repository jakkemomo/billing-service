"""Module with methods to init and release Tortoise ORM resources"""

from tortoise import Tortoise


async def tortoise_init(config: dict = None):
    """
    Init Tortoise ORM resources
    @param config: Tortoise ORM config
    """
    await Tortoise.init(config=config)
    await Tortoise.generate_schemas(safe=True)


async def tortoise_release():
    """Release Tortoise ORM resources"""
    await Tortoise.close_connections()
