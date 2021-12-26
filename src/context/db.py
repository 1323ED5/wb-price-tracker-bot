from tortoise import Tortoise
from config import DATABASE_URL


async def init():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={'models': ['src.models.item_model', 'src.models.user_model']}
    )
    await Tortoise.generate_schemas()
