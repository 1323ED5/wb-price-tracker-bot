import math
from typing import Union

from tortoise.queryset import QuerySet
from vkbottle import Keyboard, Callback

from src.helpers.text_utils import text_ellipsis


class PaginatedKeyboard:
    def __init__(self, query_set: QuerySet, per_page: int, display_field: str, item_cmd: str):
        self.query_set = query_set
        self.per_page = per_page
        self.display_field = display_field
        self.item_cmd = item_cmd

    async def get_page(self, page: Union[int, str]) -> int:
        page = int(page)

        if page < 1:
            return 1

        count = await self.query_set.all().count()
        last_page_index = math.ceil(count / self.per_page)

        if page > last_page_index:
            return last_page_index

        return page

    async def get(self, page: Union[int, str]) -> str:
        page = await self.get_page(page)

        offset = self.per_page * (page - 1)
        limit = self.per_page

        items = await self.query_set.offset(offset).limit(limit)

        kb = Keyboard(inline=True)

        count = await self.query_set.all().count()
        last_page_index = math.ceil(count / self.per_page)

        for item in items:
            text = text_ellipsis(getattr(item, self.display_field))
            payload = {"cmd": self.item_cmd, "pk": item.pk}

            kb.row().add((Callback(text, payload=payload)))

        if count > self.per_page:
            kb.row()

        if page > 1:
            payload = {"cmd": "list_chevron_left", "page": page - 1}
            kb.add(Callback("<", payload=payload))

        if page < last_page_index:
            payload = {"cmd": "list_chevron_right", "page": page + 1}
            kb.add(Callback(">", payload=payload))

        return kb.get_json()
