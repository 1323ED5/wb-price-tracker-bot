from src.models.user_model import User


async def create_user(user_id: int):
    return await User.create(id=user_id)


async def find_or_create_user(user_id: int):
    return await User.get_or_create(id=user_id)
