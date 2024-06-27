import re
import string

from aiogram import F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from FSM import States
from config import WORD_LENGTH
from core import Routers, BotControl
from core.markups import TextWidget
from private_markups import SuggestWord

commands_router = Routers.private()


class BotCommands:
    offer_word = Command("offer_word")

    @classmethod
    def commands(cls):
        return [BotCommand(command="/offer_word", description=f"Suggest a word")]


@commands_router.message(BotCommands.offer_word)
async def offer_word(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.append(SuggestWord())


@commands_router.message(StateFilter(States.input_text_suggest_word), F.text)
async def offer_word(message: Message, bot_control: BotControl):
    word = message.text.translate(str.maketrans("", "", string.punctuation.replace("-", "") + "№\n "))
    await message.delete()

    suggest: SuggestWord = bot_control.current
    if len(word) > WORD_LENGTH or not re.fullmatch(r"[a-zA-Z-]+", word):
        suggest.add_texts_rows(TextWidget(text="Incorrect input"))
        await bot_control.set_current(suggest)
        return

    offer = bot_control.bot_storage.get("offer", set())

    offer.add(word)
    bot_control.bot_storage["offer"] = offer

    suggest.suggest_another_word_display(word)
    await bot_control.set_current(suggest)
