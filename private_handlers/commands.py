import re

from aiogram import F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from FSM import States
from cache import Cache
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
        f"Enter the english word or short phrase {Emoji.PENCIL}",
        back_text=Emoji.BACK,
        state=States.input_text_new_eng_word
    ))


@commands_router.message(StateFilter(States.input_text_new_eng_word), F.text)
async def offer_new_eng_word(message: Message, bot_control: BotControl, cache: Cache):
    word = message.text
    await message.delete()

    if len(word) > ENG_LENGTH:
        await bot_control._update_text_message(
            Input,
            f"Max english word or phrase length is {ENG_LENGTH} symbols",
            back_text=Emoji.BACK,
            state=States.input_text_new_eng_word
        )
        return

    if not re.fullmatch(r"[a-zA-Z- ]+", word):
        await bot_control._update_text_message(
            Input,
            f"English word or phrase must contains only ASCII symbols {Emoji.CRYING_CAT}",
            back_text=Emoji.BACK,
            state=States.input_text_new_eng_word
        )
        return

    cache.new_eng_word = word
    await bot_control._update_text_message(
        Input,
        f"Enter the word(s)`s or phrase`s for translate {Emoji.OPEN_BOOK}\n"
        f'Format: "word" OR "some phrase, another phrase" OR "word, synonym"',
        back_text=Emoji.BACK,
        state=States.input_text_new_rus_word
    )


@commands_router.message(StateFilter(States.input_text_new_rus_word), F.text)
async def accept_input_translate(message: Message, bot_control: BotControl, cache: Cache):
    translate = message.text
    await message.delete()

    if len(translate) > ENG_LENGTH:
        await bot_control._update_text_message(
            Input,
            f"Max translate word or phrase length is {ENG_LENGTH} symbols",
            back_text=Emoji.BACK,
            state=States.input_text_new_rus_word
        )
        return

    if not re.fullmatch(r"[а-яА-Я-, ]+", translate):
        await bot_control._update_text_message(
            Input,
            f'Available translate format: "word" OR "some phrase, another phrase" OR "word, synonym"',
            back_text=Emoji.BACK,
            state=States.input_text_new_eng_word
        )
        return

    cache.replenish_offer(translate)
    await bot_control._update_text_message(
        Input,
        f'"{cache.new_eng_word} -> {translate}" sent.\nEnter the english word or short phrase: {Emoji.PENCIL}',
        back_text=Emoji.BACK,
        state=States.input_text_new_eng_word
    )
