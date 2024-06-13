import random

from aiogram import F
from aiogram.types import CallbackQuery

import cache
from FSM import States
from core.markups.text_messages import Input
from database.queries import select_words
from core import BotControl, Info, Routers
from core.tools import Emoji

english_router = Routers.private()


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    """
    0 -> eng
    1 -> translate
    :param callback:
    :param bot_control:
    :return:
    """
    words = [[word.eng, word.translate, None] for word in await select_words()]
    if not words:
        await bot_control.update_text_message(Info, f"No words so far {Emoji.CRYING_CAT}\n"
                                              f"You can send the new word to Tuurngaid /offer_word")
        return

    index = random.randint(0, len(words) - 1)
    cache.word_index = index
    word = words[index]

    side = random.randint(0, 1)
    words[index][-1] = side

    bot_control.words = words

    if side:
        content = ', '.join(word[side])
        state = States.input_text_eng_word
    else:
        content = word[side]
        state = States.input_text_rus_word

    await bot_control.update_text_message(
        Input,
        f"Translate: {content}",
        state=state
    )
