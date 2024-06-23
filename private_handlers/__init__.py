from asyncio import gather
from random import shuffle
from typing import List

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from api import SuperEnglishDictionary
from config import WORD_LENGTH
from core.markups import Input, Info

from database.queries import select_words, insert_user
from core import BotControl, Routers
from private_markups import English
from tools import Emoji

english_router = Routers.private()


async def shuffle_deck(words: List[str], bot_control: BotControl, size: int):
    shuffle(words)
    cards = await gather(*(SuperEnglishDictionary.extract_data(word) for word in words[:size]))
    c = English(cards)
    c.draw_card()
    await bot_control.set_current(
        c
    )


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    await insert_user(bot_control.user_id)
    words = await select_words()
    if words:
        if len(words) == 1:
            await shuffle_deck(words, bot_control, 1)
        else:
            await bot_control.append(Input(
                f"How many words do you want to repeat?\nEnter a integer at 1 to {len(words)}",
                state=States.input_text_how_many_words
            ))
        return

    await bot_control.append(Info(f"No words so far {Emoji.CRYING_CAT}\nYou can suggest a word to Tuurngaid /offer_word"))


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

    await shuffle_deck(words, bot_control, value)


@english_router.message(States.input_text_word_translate, F.text)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl):
    answer = message.text
    await message.delete()

    if len(answer) > WORD_LENGTH:
        await bot_control.append(Info(f"Max symbols is {WORD_LENGTH} {Emoji.CRYING_CAT}"))
        return

    c: English = bot_control.current
    c.process_answer(answer)

    await bot_control.set_current(c)


@english_router.callback_query(F.data == "reference")
async def reference(callback: CallbackQuery, bot_control: BotControl):
    c: English = bot_control.current
    c.reference()
    await bot_control.append(c)


@english_router.callback_query(F.data == "draw_card")
async def draw_card(callback: CallbackQuery, bot_control: BotControl):
    c: English = bot_control.current
    try:
        c.draw_card()
    except IndexError:
        c.result()
    await bot_control.set_current(c)
