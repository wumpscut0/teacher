from re import Match

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from FSM import States
from core import BotControl, Routers
from core.markups import Info
from group_markups.shop import InputContent
from tools import Emoji

admin_shop_router = Routers.group()


@admin_shop_router.callback_query(F.data == "init_add_content")
async def add_content(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.append(InputContent())


@admin_shop_router.message(StateFilter(States.input_photo_audio_add_content), F.content_type.in_({"audio", "photo"}))
async def accept_content(message: Message, bot_control: BotControl):
    current: InputContent = await bot_control.current()
    if message.photo:
        current.photo = message.photo[0].file_id
        current.type = message.content_type
    elif message.audio:
        current.voice = message.audio.file_id
        current.type = message.content_type
    await message.delete()

    current.edit_display()
    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "edit_name")
async def edit_name(callback: CallbackQuery, bot_control: BotControl):
    current: InputContent = await bot_control.current()
    current.input_name_display()
    await bot_control.set_current(current)


@admin_shop_router.message(StateFilter(States.input_text_content_name), F.text.regexp(r".{1,20}").as_("name"))
async def accept_name(message: Message, bot_control: BotControl, name: Match[int]):
    await message.delete()
    current: InputContent = await bot_control.current()
    current.temp_name = name.group()
    current.edit_display()
    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "edit_dna_cost")
async def edit_dna_cost(callback: CallbackQuery, bot_control: BotControl):
    current: InputContent = await bot_control.current()
    current.input_dna_cost_display()
    await bot_control.set_current(current)


@admin_shop_router.message(StateFilter(States.input_integer_dna_cost), F.text.regexp(r"\d+").as_("cost"))
async def accept_dna_cost(message: Message, bot_control: BotControl, cost: Match[int]):
    await message.delete()
    current: InputContent = await bot_control.current()
    current.temp_dna_cost = cost.group()
    current.edit_display()
    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "edit_cube_cost")
async def edit_cube_cost(callback: CallbackQuery, bot_control: BotControl):
    current: InputContent = await bot_control.current()
    current.input_cube_cost_display()
    await bot_control.set_current(current)


@admin_shop_router.message(StateFilter(States.input_integer_cube_cost), F.text.regexp(r"\d+").as_("cost"))
async def accept_dna_cost(message: Message, bot_control: BotControl, cost: Match[int]):
    await message.delete()
    current: InputContent = await bot_control.current()
    current.temp_cube_cost = cost.group()
    current.edit_display()
    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "edit_star_cost")
async def edit_dna_cost(callback: CallbackQuery, bot_control: BotControl):
    current: InputContent = await bot_control.current()
    current.input_star_cost_display()
    await bot_control.set_current(current)


@admin_shop_router.message(StateFilter(States.input_integer_star_cost), F.text.regexp(r"\d+").as_("cost"))
async def accept_star_cost(message: Message, bot_control: BotControl, cost: Match[int]):
    await message.delete()
    current: InputContent = await bot_control.current()
    current.temp_star_cost = cost.group()
    current.edit_display()
    await bot_control.set_current(current)


@admin_shop_router.callback_query(F.data == "add_content")
async def add_content(callback: CallbackQuery, bot_control: BotControl):
    current: InputContent = await bot_control.current()
    if current.temp_name == Emoji.RED_QUESTION:
        await bot_control.append(Info("Name required"))
        return

    shop = await bot_control.bot_storage.get_value_by_key("shop", {})

    if current.temp_name in shop:
        await bot_control.append(Info(f"Name {current.temp_name} already exist"))
        return

    shop[current.temp_name] = {
        "content": current.photo if current.type == "photo" else current.voice,
        "cost": {
            Emoji.DNA: current.temp_dna_cost,
            Emoji.CUBE: current.temp_cube_cost,
            Emoji.STAR: current.temp_star_cost
        }
    }
    await bot_control.bot_storage.set_value_by_key("shop", shop)

    await bot_control.pop_last()
    await bot_control.append(Info(f"Content by name {current.temp_name} added"
                                  f" {Emoji.PHOTO if current.type == "photo" else Emoji.AUDIO}"))
