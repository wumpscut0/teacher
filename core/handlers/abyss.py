from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core import BotControl
from core.markups import Info
from tools import Emoji

abyss_router = Router()


@abyss_router.callback_query(F.data == "back")
async def back(message: Message, bot_control: BotControl):
    await bot_control.back()


@abyss_router.callback_query(F.data == "flip_left")
async def flip_left(message: Message, bot_control: BotControl):
    markup = await bot_control.get_current()
    markup.reset()
    markup.page -= 1
    await bot_control.set_current(markup)


@abyss_router.callback_query(F.data == "flip_right")
async def flip_right(message: Message, bot_control: BotControl):
    markup = await bot_control.get_current()
    markup.page += 1
    await bot_control.set_current(markup)


@abyss_router.callback_query()
async def callback_abyss(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.append(Info(f"Sorry. This button no working so far. {Emoji.CRYING_CAT}"))


@abyss_router.message(~StateFilter(None))
async def wrong_type_message_abyss(message: Message, bot_control: BotControl, state: FSMContext):
    try:
        await message.delete()
    except TelegramBadRequest:
        await bot_control.clear_chat(force=True)
        await bot_control.refresh()

    state_name = await state.get_state()
    guess = ""
    if "text" in state_name:
        guess = "text"
    elif "integer" in state_name:
        guess = "integer"
    elif "photo" in state_name:
        guess = "photo"

    if guess:
        guess = f"Try to send {guess}"
    await bot_control.append(Info(
        f"Wrong message type {Emoji.BROKEN_HEARTH} {guess}"
    ))


@abyss_router.message()
async def message_abyss(message: Message, bot_control: BotControl):
    if message.photo:
        for photo in message.photo:
            print(f"Photo: {photo.file_id} {message.photo}")
    elif message.video:
        print(f"Video: {message.video.file_id} {message.video}")
    elif message.voice:
        print(f"Voice: {message.voice.file_id} {message.voice}")
    elif message.audio:
        print(f"Audio: {message.audio.file_id} {message.audio}")

    try:
        await message.delete()
    except TelegramBadRequest:
        await bot_control.clear_chat(force=True)
        await bot_control.refresh()
        return
