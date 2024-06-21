import re
import string

from aiogram import F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from FSM import States
from cache import Offer
from config import WORD_LENGTH
from core import Routers, BotControl
from core.markups import Input
from tools import Emoji

commands_router = Routers.private()


class BotCommands:
    offer_word = Command("offer_word")

    @classmethod
    def commands(cls):
        return [BotCommand(command="/offer_word", description=f"Suggest a word")]


@commands_router.message(BotCommands.offer_word)
async def offer_word(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.append(await Input(
        "Suggest a ENGLISH word to Tuurngait that goes in the English Run.",
        back_text=Emoji.BACK,
        state=States.input_text_suggest_word
    ).update())


@commands_router.message(StateFilter(States.input_text_suggest_word), F.text)
async def offer_word(message: Message, bot_control: BotControl):
    word = message.text.translate(str.maketrans("", "", string.punctuation.replace("-", "") + "№\n "))
    await message.delete()

    if len(word) > WORD_LENGTH or not re.fullmatch(r"[a-zA-Z-]+", word):
        await bot_control.set_last(await Input(
            "Suggest a ENGLISH word to Tuurngait that goes in the English Run.\n"
            "Your input incorrect.",
            back_text=Emoji.BACK,
            state=States.input_text_suggest_word
        ).update())
        return

    Offer().append(word)
    await bot_control.set_last(await Input(
            f'"{word}" sent.\n\nSuggest another word',
            back_text=Emoji.BACK,
            state=States.input_text_suggest_word
        ).update())
