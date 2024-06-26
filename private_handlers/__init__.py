from asyncio import gather
from random import shuffle

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from api import SuperEnglishDictionary
from config import WORD_LENGTH
from core.markups import Info

from core import BotControl, Routers
from private_markups import English
from tools import Emoji

english_router = Routers.private()


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    words = bot_control.bot_storage.get("words")

    if not words:
        await bot_control.append(
            Info(f"No words so far {Emoji.CRYING_CAT}\nYou can suggest a word to Tuurngaid /offer_word")
        )
        return

    word_data = [
        card for card in
        (await gather(*(SuperEnglishDictionary.extract_data(word) for word in words)))
        if card is not None
    ]
    cards = [card for word in word_data for card in word.cards]

    shuffle(cards)

    knowledge = bot_control.user_storage.get("english:knowledge", {})

    english = English(cards, knowledge, bot_control.user_storage.get("english:total_dna", 0))
    await bot_control.append(
        english
    )


@english_router.message(States.input_text_word_translate, F.text)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl):
    answer = message.text
    await message.delete()

    if len(answer) > WORD_LENGTH:
        await bot_control.append(Info(f"Max symbols is {WORD_LENGTH} {Emoji.CRYING_CAT}"))
        return

    english: English = bot_control.current
    english.process_answer(answer)
    bot_control.user_storage["english:knowledge"] = english.knowledge
    bot_control.user_storage["english:total_dna"] = bot_control.user_storage.get("english:total_dna", 0) + english.temp_dna
    await bot_control.set_current(english)


@english_router.callback_query(F.data == "reference")
async def reference(callback: CallbackQuery, bot_control: BotControl):
    english: English = bot_control.current
    english.reference()
    await bot_control.append(english)


@english_router.callback_query(F.data == "draw_card")
async def draw_card(callback: CallbackQuery, bot_control: BotControl):
    english: English = bot_control.current
    try:
        english.draw_card()
    except IndexError:
        english.result()

    await bot_control.set_current(english)


@english_router.callback_query(F.data == "result_english_run")
async def result_english_run(callback: CallbackQuery, bot_control: BotControl):
    english: English = bot_control.current
    english.result()
    await bot_control.set_current(english)
