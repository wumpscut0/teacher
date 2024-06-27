from asyncio import gather
from random import shuffle

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from api import SuperEnglishDictionary
from core.markups import Info

from core import BotControl, Routers
from private_markups import English
from tools import Emoji

english_router = Routers.private()


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    words = await bot_control.bot_storage.get_value_by_key("words")

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

    knowledge = await bot_control.user_storage.get_value_by_key("english:knowledge", {})
    dna = await bot_control.user_storage.get_value_by_key("english:total_dna", 0)

    english = English(cards, knowledge, dna)
    await bot_control.append(
        english
    )


@english_router.message(States.input_text_word_translate, F.text)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl):
    answer = message.text
    await message.delete()

    if len(answer) > 200:
        await bot_control.append(Info(f"Max symbols is {200} {Emoji.CRYING_CAT}"))
        return

    english: English = await bot_control.current()
    english.process_answer(answer)
    await bot_control.user_storage.set_value_by_key("english:knowledge", english.knowledge)
    await bot_control.user_storage.set_value_by_key("english:total_dna", english.total_dna + english.temp_dna)
    await bot_control.set_current(english)


@english_router.callback_query(F.data == "reference")
async def reference(callback: CallbackQuery, bot_control: BotControl):
    english: English = await bot_control.current()
    english.reference()
    await bot_control.append(english)


@english_router.callback_query(F.data == "draw_card")
async def draw_card(callback: CallbackQuery, bot_control: BotControl):
    english: English = await bot_control.current()
    try:
        english.draw_card()
    except IndexError:
        english.result()

    await bot_control.set_current(english)


@english_router.callback_query(F.data == "result_english_run")
async def result_english_run(callback: CallbackQuery, bot_control: BotControl):
    english: English = await bot_control.current()
    english.result()
    await bot_control.set_current(english)
