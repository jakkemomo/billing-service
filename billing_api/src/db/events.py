from tortoise import Tortoise


async def tortoise_init(config: dict = None):
    await Tortoise.init(config=config)
    await Tortoise.generate_schemas(safe=True)


async def tortoise_release():
    await Tortoise.close_connections()
