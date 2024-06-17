import random
from copy import copy

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from core.markups import Input, Info

from database.queries import select_words
from core import BotControl, Routers
from core.tools import Emoji
from private_markups import English, Card

english_router = Routers.private()


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    words = await select_words()
    await bot_control.dig(Input(
        f"How many words do you want to repeat?\nEnter a integer at 1 to {len(words)}\n\n",
        state=States.input_text_how_many_words
    ))


@english_router.message(States.input_text_how_many_words)
async def accept_input_text_how_many_words(message: Message, bot_control: BotControl):
    value = message.text
    await message.delete()

    words = await select_words()
    try:
        value = int(value)
    except ValueError:
        return
    if not 1 <= value <= len(words):
        return

    cards = [Card(question=word.eng, answer=', '.join(word.translate)) for word in words]
    cards.extend([Card(question=card.answer, answer=card.question) for card in cards])

    if not words:
        await bot_control.dream(Info(
            f"No words so far {Emoji.CRYING_CAT}\n"
            f"You can offer a new word /offer_word"
        ))
        return

    random.shuffle(cards)
    await bot_control.dream(
        English(cards[:value * 2])
    )

# TODO finalize
@english_router.message(States.input_text_word_translate)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl):
    answer = message.text
    await message.delete()
    english: English = await bot_control.get_current_point()
    english.answer = answer
    await english.init()
    english.init_control()
    fresh_markup = copy(english)
            fresh_markup.text_map = []
            fresh_markup.keyboard_map = [[]]
            self._context_storage.dream(fresh_markup)
        await self._state.set_state(raw_markup.state)
    except AttributeError:
        await self._come_out()
        raise ValueError("Error with trying init raw markup")
    await bot_control.dream(english)
