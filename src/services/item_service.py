from typing import Union, List

from src.models.item_model import Item


async def create_item(item_id: int, name: str, price: Union[int, float], image: str):
    return await Item.create(
        id=item_id,
        name=name,
        price=price,
        image=image
    )


async def get_item(item_id: int) -> Union[Item, None]:
    return await Item.get_or_none(id=item_id)


async def find_or_create_item(item_data: dict):
    data = item_data.copy()
    item_id = data['id']
    del data['id']

    return await Item.get_or_create(defaults=data, id=item_id)


async def get_all_items() -> List[Item]:
    return await Item.all()
