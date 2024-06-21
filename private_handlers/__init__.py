from asyncio import gather
from random import shuffle
from typing import List

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from api import WordData, SuperEnglishDictionary
from config import WORD_LENGTH
from core.markups import Input, Info

from database.queries import select_words
from core import BotControl, Routers
from private_markups import English
from tools import Emoji

english_router = Routers.private()


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    words = await select_words()
    await bot_control.extend(await Input(
        f"How many words do you want to repeat?\nEnter a integer at 1 to {len(words)}\n\n",
        state=States.input_text_how_many_words
    ).update())


@english_router.message(States.input_text_how_many_words, F.text)
async def accept_input_text_how_many_words(message: Message, bot_control: BotControl):
    value = message.text
    await message.delete()

    try:
        value = int(value)
    except ValueError:
        return

    words = await select_words()
    if not 1 <= value <= len(words):
        return

    shuffle(words)
    cards = await gather(*(SuperEnglishDictionary.extract_data(word) for word in words[:value]))

    if not words:
        await bot_control.set_last(await Info(
            f"No words so far {Emoji.CRYING_CAT}\n"
            f"You can offer a new word /offer_word"
        ).update())
        return

    await bot_control.set_last(
        English(cards)
    )


@english_router.message(States.input_text_word_translate, F.text)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl):
    answer = message.text
    await message.delete()
    if len(answer) > WORD_LENGTH:
        await bot_control.extend(await Info(f"Max symbols is {WORD_LENGTH} {Emoji.CRYING_CAT}").update())
        return

    await bot_control.set_last(await bot_control.last.update(answer))
