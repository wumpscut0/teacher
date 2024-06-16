import re

from aiogram import F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from FSM import States
from config import ENG_LENGTH
from core import Routers, BotControl, Emoji
from core.markups.text_messages import Input

commands_router = Routers.private()


class BotCommands:
    offer_word = Command("offer_word")

    @classmethod
    def commands(cls):
        return [BotCommand(command="/offer_word", description=f"Предложить новое слово")]


@commands_router.message(BotCommands.offer_word)
async def offer_word(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.dig(Input(
        f"Enter the english word or short phrase {Emoji.PENCIL}\n\n"
        f"Max english word or phrase length is {ENG_LENGTH} symbols\n"
        f"English word or phrase must contains only [latin letters, -, spaces] symbols",
        back_text=Emoji.BACK,
        state=States.input_text_new_eng_word
    ))


@commands_router.message(StateFilter(States.input_text_new_eng_word), F.text)
async def offer_new_eng_word(message: Message, bot_control: BotControl):
    word = message.text
    await message.delete()

    if len(word) > ENG_LENGTH or not re.fullmatch(r"[a-zA-Z- ]+", word):
        return

    bot_control.user_storage.new_eng_word = word
    await bot_control.dream(Input(
        f"Enter the word(s)`s or phrase`s for translate {Emoji.OPEN_BOOK}\n\n"
        f'Format: "word" OR "some phrase, another phrase" OR "word, synonym\n"'
        f'Max translate word or phrase length is {ENG_LENGTH} symbols"\n',
        back_text=Emoji.BACK,
        state=States.input_text_new_rus_word
    ))


@commands_router.message(StateFilter(States.input_text_new_rus_word), F.text)
async def accept_input_translate(message: Message, bot_control: BotControl):
    translate = message.text
    await message.delete()

    if len(translate) > ENG_LENGTH or not re.fullmatch(r"[а-яА-Я-, ]+", translate):
        return

    bot_control.user_storage.replenish_offer(translate)
    await bot_control.dream(Input(
        f'"{bot_control.user_storage.new_eng_word} -> {translate}" sent.\n\nEnter the english word or short phrase: {Emoji.PENCIL}',
        back_text=Emoji.BACK,
        state=States.input_text_new_eng_word
    ))
