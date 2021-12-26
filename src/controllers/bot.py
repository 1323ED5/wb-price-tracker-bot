from typing import Union

from tortoise.queryset import QuerySet
from vkbottle import Keyboard, Text, ShowSnackbarEvent, Callback, KeyboardButtonColor
from vkbottle.bot import Message, rules
from vkbottle.tools import PhotoMessageUploader
from vkbottle_types import GroupTypes
from vkbottle_types.events import GroupEventType

import src.messages as messages
from src.context.vk import bot
from src.helpers.paginated_keyboard import PaginatedKeyboard
from src.parser import download_photo, parse_item, parse_item_id
from src.services.item_service import find_or_create_item, get_item
from src.services.user_service import find_or_create_user


async def get_keyboard(query_set: QuerySet, page: Union[int, str]) -> str:
    """Its generate paginated keyboard"""

    paginated_kb = PaginatedKeyboard(
        query_set=query_set,
        per_page=4,
        display_field="name",
        item_cmd="show_item_info"
    )
    return await paginated_kb.get(page)


@bot.on.private_message(text="Начать")
async def start(message: Message):
    """
    Sends welcome message
    """
    kb = Keyboard().add(Text("Список")).get_json()
    from_id = message.from_id
    await find_or_create_user(from_id)
    await message.answer(messages.WELCOME, keyboard=kb)


@bot.on.private_message(rules.RegexRule(r'^https:\/\/www\.wildberries\.ru\/catalog\/\d+\/detail\.aspx'))
async def track_item(message: Message):
    """
    Its getting the item id from the url and append it to the user tracking list
    """

    from_id = message.from_id

    item_id = parse_item_id(message.text)
    item_data = await parse_item(item_id)

    user, _ = await find_or_create_user(from_id)
    item, _ = await find_or_create_item(item_data)

    await item.subscribers.add(user)
    await item.save()

    msg = messages.NOW_YOU_TRACKING.format(item_data['name'])
    await message.answer(msg)


@bot.on.private_message(text="Список")
async def items_list(message: Message):
    """
    It show the list of tracking items
    """

    from_id = message.from_id

    user, _ = await find_or_create_user(from_id)
    items = await user.items.all()

    if not len(items):
        return await message.answer(messages.ITEM_LIST_EMPTY)

    kb = await get_keyboard(user.items, 1)

    await message.answer(message=messages.ITEM_LIST_HEADER, keyboard=kb)


async def detail_item_handler(event):
    """
    It shows a detailed information about the item from the item list
    """

    from_id = event.object.user_id
    payload = event.object.payload
    conversation_message_id = event.object.conversation_message_id

    item = await get_item(payload['pk'])

    image_bytes = await download_photo(item.image)
    image_attachment = await PhotoMessageUploader(bot.api).upload(
        file_source=image_bytes,
        peer_id=from_id
    )

    back_to_list_btn_payload = {"cmd": "list_chevron_right", "page": 1}
    back_to_list_btn = Callback("Назад к списку", payload=back_to_list_btn_payload)

    delete_item_btn_payload = {"cmd": "delete_item", "pk": payload['pk']}
    delete_item_btn = Callback("Не отслеживать", payload=delete_item_btn_payload)

    kb = Keyboard(inline=True)
    kb.add(back_to_list_btn)
    kb.add(delete_item_btn, color=KeyboardButtonColor.NEGATIVE)
    kb = kb.get_json()

    item_url = f"https://www.wildberries.ru/catalog/{item.id}/detail.aspx"

    await bot.api.messages.edit(
        peer_id=from_id,
        message=f"{item.name}\n{item_url}",
        keyboard=kb,
        random_id=0,
        conversation_message_id=conversation_message_id,
        attachment=image_attachment,
        dont_parse_links=1
    )


async def delete_item_handler(event):
    """
    It removes an item from tracking and brings you back to the item list
    """
    from_id = event.object.user_id
    payload = event.object.payload
    conversation_message_id = event.object.conversation_message_id

    user, _ = await find_or_create_user(from_id)

    to_delete = await user.items.filter(id=payload['pk'])
    await user.items.remove(to_delete[0])

    if not await user.items.all().count():
        await bot.api.messages.edit(
            peer_id=from_id,
            message="Вы ничего не отслеживаете, отправьте ссылку на товар чтобы начать",
            random_id=0,
            conversation_message_id=conversation_message_id
        )
        return

    event.object.payload['page'] = 1
    await chevron_handler(event)


async def chevron_handler(event):
    """
    It handle chevron buttons on the bottom of the item list
    """

    from_id = event.object.user_id
    payload = event.object.payload
    conversation_message_id = event.object.conversation_message_id

    user, _ = await find_or_create_user(from_id)

    kb = await get_keyboard(user.items, payload['page'])

    await bot.api.messages.edit(
        peer_id=from_id,
        message=messages.ITEM_LIST_HEADER,
        keyboard=kb,
        random_id=0,
        conversation_message_id=conversation_message_id
    )


async def event_handler_error(event):
    """
    If any callback button results in an error, this handler shows the snackbar message
    """

    event_id = event.object.event_id
    user_id = event.object.user_id
    peer_id = event.object.peer_id
    event_data = ShowSnackbarEvent(text=messages.SNACKBAR_ERROR).json()

    await bot.api.messages.send_message_event_answer(
        event_id=event_id,
        user_id=user_id,
        peer_id=peer_id,
        event_data=event_data,
    )


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=GroupTypes.MessageEvent)
async def handle_message_event(event: GroupTypes.MessageEvent):
    """It gets message event from callback button and puts it on required handler"""

    commands = {
        "list_chevron_left": chevron_handler,
        "list_chevron_right": chevron_handler,
        "delete_item": delete_item_handler,
        "show_item_info": detail_item_handler,
    }

    handler = commands.get(
        event.object.payload['cmd'],
        event_handler_error
    )

    try:
        await handler(event)
    except Exception as e:
        await event_handler_error(event)
        print(e)
