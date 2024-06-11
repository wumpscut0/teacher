import random

from aiogram import Router, F
from aiogram.types import CallbackQuery

from alt_aiogram.FSM import States
from alt_aiogram.markups.text_messages import Input
from alt_aiogram.redis import Tuurngaid
from database.queries import select_words
from alt_aiogram import BotControl, Info
from tools import Emoji

english = Router()


@english.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    words = [[word.eng, word.rus, None] for word in await select_words()]
    if not words:
        await bot_control.update_text_message(Info, f"No words so far {Emoji.CRYING_CAT}\n"
                                              f"You can send the new word to Tuurngaid /offer_word")
        return

    index = random.randint(0, len(words) - 1)
    Tuurngaid.word_index = index
    word = words[index]

    side = random.randint(0, 1)
    word[-1] = side

    Tuurngaid.words = words

    if side:
        state = States.input_text_eng_word
    else:
        state = States.input_text_rus_word

    await bot_control.update_text_message(
        Input,
        f"Enter the translate for word: {word[side]}",
        state=state
    )
