import os
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
from private_markups import Translate, Reward

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

    words = [[word.eng, ', '.join(word.translate)] for word in words]
    words.extend([[translate, eng] for eng, translate in words])

    if not words:
        await bot_control.dream(Info(
            f"No words so far {Emoji.CRYING_CAT}\n"
            f"You can offer a new word /offer_word"
        ))
        return

    bot_control.user_storage.possible_scores = value * 2
    bot_control.user_storage.score = 0
    random.shuffle(words)
    bot_control.user_storage.words = words[:value * 2]
    await bot_control.dream(
        Translate(bot_control.chat_id)
    )


@english_router.message(States.input_text_word_translate)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl):
    answer = message.text
    await message.delete()

    cache: Cache = bot_control.user_storage
    score = cache.score
    for threshold in range(5, cache.possible_scores, 5):
        if threshold == score:
            rewards = cache.rewards
            if not rewards[threshold]:
                rewards[threshold] = 1
            cache.rewards = rewards
            point = await bot_control.get_current_point()
            await bot_control.dream(Reward(
                FSInputFile(os.path.join(os.path.dirname(__file__), f"../images/{threshold}.jpg")),
                point.text_map,
                point.keyboard_map
            ))
            break
    else:
        await bot_control.dream(Translate(bot_control.chat_id, answer))