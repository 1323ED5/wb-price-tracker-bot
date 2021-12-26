import re
from typing import Union, TypedDict

import aiohttp

from src.helpers.decorators import async_infinity_loop
import src.messages as messages
from src.context.vk import bot
from src.services.item_service import get_all_items


class ItemData(TypedDict):
    id: int
    price: Union[float, int]
    name: str
    image: str


async def fetch_json(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()


def parse_item_id(raw_url):
    pattern = r"^https:\/\/www\.wildberries\.ru\/catalog\/(\d+)\/detail\.aspx"
    match_obj = re.match(pattern, raw_url)
    item_id = match_obj.groups()[0]
    return int(item_id)


async def parse_item(item_id: int) -> ItemData:
    url = f"https://napi.wildberries.ru/api/catalog/{item_id}/detail.aspx"
    data = (await fetch_json(url))['data']

    brand_name = data['productInfo']['brandName']
    item_name = data['productInfo']['name']
    name = f"[{brand_name}] {item_name}"

    image = f"http://{data['colors'][0]['previewUrl'][2:]}"

    price = data['colors'][0]['nomenclatures'][0]['rawMinPriceWithSale']

    return {
        "id": item_id,
        "price": price,
        "name": name,
        "image": image
    }


async def download_photo(url) -> bytes:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()


async def spread(message, subscribers):
    for user in subscribers:
        bot.api.message(
            peer_id=user.id,
            message=message,
            random_id=0
        )


@async_infinity_loop(60 * 60)
async def parsing_loop():
    items = await get_all_items()

    for item in items:
        parsed = await parse_item(item.id)

        if parsed['price'] >= item.price:
            item.price = parsed['price']
            await item.save()
            continue

        subscribers = await item.subscribers.all()
        msg = messages.ITEM_BECOME_CHEAPER.format(item.name, item.price, parsed['price'])
        await spread(msg, subscribers)

        item.price = parsed['price']
        await item.save()
