import random

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from config import ENG_LENGTH
from core.markups import Input, Info

from database.queries import select_words
from core import BotControl, Routers
from core.tools import Emoji
from private_markups import English, Card

english_router = Routers.private()


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    words = await select_words()
    await bot_control.dig(await Input(
        f"How many words do you want to repeat?\nEnter a integer at 1 to {len(words) * 2}\n\n",
        state=States.input_text_how_many_words
    ).update())


@english_router.message(States.input_text_how_many_words, F.text)
async def accept_input_text_how_many_words(message: Message, bot_control: BotControl):
    value = message.text
    await message.delete()

    words = await select_words()
    try:
        value = int(value)
    except ValueError:
        return
    if not 1 <= value <= len(words) * 2:
        return

    cards = [Card(question=word.eng, answer=', '.join(word.translate)) for word in words]
    cards.extend([Card(question=card.answer, answer=card.question) for card in cards])

    if not words:
        await bot_control.dream(await Info(
            f"No words so far {Emoji.CRYING_CAT}\n"
            f"You can offer a new word /offer_word"
        ).update())
        return

    random.shuffle(cards)
    await bot_control.dream(
        English(cards[:value])
    )


@english_router.message(States.input_text_word_translate, F.text)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl):
    answer = message.text.strip().lower()
    await message.delete()
    if len(answer) > ENG_LENGTH:
        await bot_control.dig(await Info(f"Max symbols is {ENG_LENGTH} {Emoji.CRYING_CAT}").update())
        return

    await bot_control.dream(await (await bot_control.get_raw_current_markup()).update(answer))
