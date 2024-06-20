from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core import BotControl, Info
from tools import Emoji

abyss_router = Router()


@abyss_router.callback_query(F.data == "bury")
async def bury(message: Message, bot_control: BotControl):
    await bot_control.pop_last()


@abyss_router.callback_query(F.data == "flip_left")
async def flip_left(message: Message, bot_control: BotControl):
    markup = bot_control.last
    markup.page -= 1
    bot_control.last = await markup.update()


@abyss_router.callback_query(F.data == "flip_right")
async def flip_right(message: Message, bot_control: BotControl):
    markup = bot_control.last
    markup.page += 1
    bot_control.last = await markup.update()


@abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.append(await Info(f"Sorry. This button no working so far. {Emoji.CRYING_CAT}").update())


@abyss_router.message(~StateFilter(None))
async def wrong_type_message_abyss(
    message: Message, bot_control: BotControl, state: FSMContext
):
    try:
        await message.delete()
    except TelegramBadRequest:
        await bot_control.clear_chat(force=True)
        await bot_control.push()

    state_name = await state.get_state()
    guess = ""
    if "text" in state_name:
        guess = "text"
    elif "photo" in state_name:
        guess = "photo"

    if guess:
        guess = f"Try to send {guess}"
    await bot_control.append(await Info(
        f"Wrong message type {Emoji.BROKEN_HEARTH} {guess}"
    ).update())


@abyss_router.message()
async def message_abyss(message: Message, bot_control: BotControl):
    try:
        await message.delete()
    except TelegramBadRequest:
        await bot_control.clear_chat(force=True)
        await bot_control.push()
        return
    await bot_control.append(await Info(f"Your message was eaten by the abyss {Emoji.ABYSS}").update())
