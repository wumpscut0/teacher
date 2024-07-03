from re import fullmatch
import string

from aiogram import F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from FSM import States
from core import Routers, BotControl
from core.markups import Info
from models.english import SuggestWords

commands_router = Routers.private()


class BotCommands:
    offer_word = Command("offer_word")

    @classmethod
    def commands(cls):
        return [BotCommand(command="/offer_word", description=f"Suggest a word")]


@commands_router.message(BotCommands.offer_word)
async def offer_words(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.append(SuggestWords())


@commands_router.message(StateFilter(States.input_text_suggest_word), F.text)
async def accept_offer_words(message: Message, bot_control: BotControl):
    words = message.text.translate(str.maketrans("", "", string.punctuation.replace("-", "") + "№\n")).split()
    await message.delete()
    words = set(word for word in map(lambda word: word.strip(), words) if fullmatch(r"[a-zA-Z-]+", word))
    if not words:
        await bot_control.append(Info("Incorrect input"))
        return

    offer = await bot_control.bot_storage.get_value_by_key("offer", set())
    for word in words:
        offer.add(word)
    await bot_control.bot_storage.set_value_by_key("offer", offer)

    suggest: SuggestWords = await bot_control.current()
    suggest.suggest_another_word_display(", ".join(words))
    await bot_control.set_current(suggest)
