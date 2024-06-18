from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core import BotControl, Info

from core.tools.emoji import Emoji

abyss_router = Router()


@abyss_router.callback_query(F.data == "bury")
async def bury(message: Message, bot_control: BotControl):
    await bot_control.bury()


@abyss_router.callback_query(F.data == "flip_left")
async def flip_left(message: Message, bot_control: BotControl):
    point = await bot_control.get_raw_current_markup()
    point.page -= 1
    await bot_control.dream(await point.update())


@abyss_router.callback_query(F.data == "flip_right")
async def flip_right(message: Message, bot_control: BotControl):
    point = await bot_control.get_raw_current_markup()
    point.page += 1
    await bot_control.dream(await point.update())


@abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.dig(await Info(f"Sorry. This button no working so far. {Emoji.CRYING_CAT}").update())


@abyss_router.message(~StateFilter(None))
async def wrong_type_message_abyss(
    message: Message, bot_control: BotControl, state: FSMContext
):
    try:
        await message.delete()
    except TelegramBadRequest:
        await bot_control.sleep()
        await bot_control.look_around()

    state_name = await state.get_state()
    guess = ""
    if "text" in state_name:
        guess = "text"
    elif "photo" in state_name:
        guess = "photo"

    if guess:
        guess = f"Try to send {guess}"
    await bot_control.dig(await Info(
        f"Wrong message type {Emoji.BROKEN_HEARTH} {guess}"
    ).update())


@abyss_router.message()
async def message_abyss(message: Message, bot_control: BotControl):
    try:
        await message.delete()
    except TelegramBadRequest:
        await bot_control.sleep()
        await bot_control.look_around()
        return
    await bot_control.dig(await Info(f"Your message was eaten by the abyss {Emoji.ABYSS}").update())
