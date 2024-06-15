import os.path
import random

from aiogram import F
from aiogram.types import CallbackQuery, Message, FSInputFile

from cache import Cache
from FSM import States
from core.markups.photo_messages import Photo
from core.markups.text_messages import Input
from database.queries import select_words
from core import BotControl, Info, Routers
from core.tools import Emoji
from private_markups import Translate

english_router = Routers.private()


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl, cache: Cache):
    words = await select_words()
    cache.words = words
    await bot_control._update_text_message(
        Input,
        f"How many words do you want to repeat?\nEnter a integer at 1 to {len(words)}",
        state=States.input_text_how_many_words
    )


@english_router.message(States.input_text_how_many_words)
async def accept_input_text_how_many_words(message: Message, bot_control: BotControl, cache: Cache):
    value = message.text
    await message.delete()
    try:
        value = int(value)
    except ValueError:
        await bot_control._update_text_message(
            Input,
            f"\nHow many words do you want to repeat?\nEnter a integer at 1 to {len(cache.words)}",
            state=States.input_text_how_many_words
        )
        return
    if not 1 <= value <= len(cache.words):
        await bot_control._update_text_message(
            Input,
            f"\nHow many words do you want to repeat?\nEnter a integer at 1 to {len(cache.words)}",
            state=States.input_text_how_many_words
        )
        return

    words = [[word.eng, ', '.join(word.translate)] for word in cache.words]
    words.extend([[translate, eng] for eng, translate in words])
    if not words:
        await bot_control._update_text_message(Info, f"No words so far {Emoji.CRYING_CAT}\n"
                                                    f"You can offer a new word /offer_word")
        return

    cache.possible_scores = len(words)
    cache.score = 0
    random.shuffle(words)
    cache.words = words
    word = cache.pop_word
    cache.current_word = word
    await bot_control.set_context(
        Translate, cache, new_word=word
    )


@english_router.message(States.input_text_word_translate)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl, cache: Cache):
    answer = message.text
    await message.delete()
    word = cache.pop_word
    await bot_control.set_context(Translate, cache, answer=answer, new_word=word)
    cache.current_word = word
