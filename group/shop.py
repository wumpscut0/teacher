from re import Match
from typing import Dict

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from core import BotControl
from core.markups import Info, Conform
from FSM import States
from models.shop import Content, Shop, EditContentCallbackData
from tools import Emoji
from core import Routers

admin_shop_router = Routers.group()


@admin_shop_router.callback_query(F.data == "add_content")
async def add_content(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.append(Content(action_type="add"))


@admin_shop_router.callback_query(F.data == "edit_shop")
async def edit_shop(callback: CallbackQuery, bot_control: BotControl):
    shop = await bot_control.bot_storage.get_value_by_key("shop", {})
    if not shop:
        await bot_control.append(Info(f"No content so far {Emoji.WEB}"))
        return

    await bot_control.append(Shop("edit"))


@admin_shop_router.callback_query(EditContentCallbackData.filter())
async def edit_content(callback: CallbackQuery, callback_data: EditContentCallbackData, bot_control: BotControl):
    item = (await bot_control.bot_storage.get_value_by_key("shop"))[callback_data.name]
    await bot_control.append(Content(
        action_type="edit",
        content_type=item["type"],
        content=item["content"],
        temp_name=callback_data.name,
        temp_dna_cost=item["cost"][Emoji.DNA],
        temp_cube_cost=item["cost"][Emoji.CUBE],
        temp_star_cost=item["cost"][Emoji.STAR]
    ))


@admin_shop_router.callback_query(F.data == "edit_content")
async def edit_content(callback: CallbackQuery, bot_control: BotControl):
    current: Content = await bot_control.get_current()
    current.input_content_display()
    await bot_control.append(current)


@admin_shop_router.message(StateFilter(States.input_photo_audio_content), F.content_type.in_({"photo", "audio", "voice"}))
async def accept_content(message: Message, bot_control: BotControl):
    current: Content = await bot_control.get_current()
    if message.photo:
        current.photo = message.photo[0].file_id
        current.type = message.content_type
    elif message.audio or message.voice:
        current.voice = message.audio.file_id
        current.type = message.content_type
    await message.delete()

    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "edit_name")
async def edit_name(callback: CallbackQuery, bot_control: BotControl):
    current: Content = await bot_control.get_current()
    current.input_name_display()
    await bot_control.append(current)


@admin_shop_router.message(StateFilter(States.input_text_content_name), F.text.regexp(r".{1,20}").as_("name"))
async def accept_name(message: Message, bot_control: BotControl, name: Match[int]):
    await bot_control.pop_last()
    await message.delete()
    current: Content = await bot_control.get_current()
    current.temp_name = name.group()
    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "edit_dna_cost")
async def edit_dna_cost(callback: CallbackQuery, bot_control: BotControl):
    current: Content = await bot_control.get_current()
    current.input_dna_cost_display()
    await bot_control.append(current)


@admin_shop_router.message(StateFilter(States.input_integer_dna_cost), F.text.regexp(r"\d+").as_("cost"))
async def accept_dna_cost(message: Message, bot_control: BotControl, cost: Match[int]):
    await message.delete()

    await bot_control.pop_last()
    current: Content = await bot_control.get_current()
    current.temp_dna_cost = cost.group()

    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "edit_cube_cost")
async def edit_cube_cost(callback: CallbackQuery, bot_control: BotControl):
    current: Content = await bot_control.get_current()
    current.input_cube_cost_display()
    await bot_control.append(current)


@admin_shop_router.message(StateFilter(States.input_integer_cube_cost), F.text.regexp(r"\d+").as_("cost"))
async def accept_cube_cost(message: Message, bot_control: BotControl, cost: Match[int]):
    await message.delete()

    await bot_control.pop_last()
    current: Content = await bot_control.get_current()
    current.temp_cube_cost = cost.group()

    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "edit_star_cost")
async def edit_star_cost(callback: CallbackQuery, bot_control: BotControl):
    current: Content = await bot_control.get_current()
    current.input_star_cost_display()
    await bot_control.append(current)


@admin_shop_router.message(StateFilter(States.input_integer_star_cost), F.text.regexp(r"\d+").as_("cost"))
async def accept_star_cost(message: Message, bot_control: BotControl, cost: Match[int]):
    await message.delete()

    await bot_control.pop_last()
    current: Content = await bot_control.get_current()
    current.temp_star_cost = cost.group()

    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "delete_content")
async def delete_content(callback: CallbackQuery, bot_control: BotControl):
    content: Content = await bot_control.get_current()
    await bot_control.append(Conform(f"Conform delete {content.temp_name}"
                                     f" {Emoji.PHOTO if content.type == "photo" else Emoji.AUDIO}?",
                                     yes_callback_data="conform_delete_content"))


@admin_shop_router.callback_query(F.data == "conform_delete_content")
async def conform_delete_content(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.pop_last()
    content: Content = await bot_control.get_current()
    await content.delete(bot_control)


@admin_shop_router.callback_query(F.data == "merge_content")
async def merge_content(callback: CallbackQuery, bot_control: BotControl):
    content: Content = await bot_control.get_current()
    if not content.temp_name or content.temp_name == Emoji.RED_QUESTION:
        await bot_control.append(Info("Name required"))
        return

    if content.type == "text":
        await bot_control.append(Info("Content required"))
        return

    shop = await bot_control.bot_storage.get_value_by_key("shop", {})

    if content.action_type == "add" and content.temp_name in shop:
        await bot_control.append(Info(f"Name {content.temp_name} already exist"))
        return

    if content.action_type == "edit":
        shop.pop(content.temp_old_name)

    shop[content.temp_name] = {
        "type": content.type,
        "content": content.photo if content.type == "photo" else content.voice,
        "cost": {
            Emoji.DNA: int(content.temp_dna_cost),
            Emoji.CUBE: int(content.temp_cube_cost),
            Emoji.STAR: int(content.temp_star_cost)
        }
    }
    await bot_control.bot_storage.set_value_by_key("shop", shop)
    await bot_control.back(True)
