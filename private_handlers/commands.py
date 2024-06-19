import re

from aiogram import F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, BotCommand

from FSM import States
from cache import Offer
from config import ENG_LENGTH
from core import Routers, BotControl, Emoji
from core.markups import Input
from database.models import WordModel

commands_router = Routers.private()


def replenish_offer(self, translate: str):
    Offer().replenish_offer(WordModel(eng=self.new_eng_word, translate=translate.split(", ")))


class BotCommands:
    offer_word = Command("offer_word")

    @classmethod
    def commands(cls):
        return [BotCommand(command="/offer_word", description=f"Suggest a word")]


@commands_router.message(BotCommands.offer_word)
async def offer_word(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.dig(await Input(
        "Suggest a ENGLISH/RUSSIAN word to Tuurngait that goes in the English Run.",
        back_text=Emoji.BACK,
        state=States.input_text_new_eng_word
    ).update())


@commands_router.message(StateFilter(States.input_text_new_eng_word), F.text)
async def offer_new_eng_word(message: Message, bot_control: BotControl):
    word = message.text
    await message.delete()

    if len(word) > ENG_LENGTH or not re.fullmatch(r"[a-zA-Z- ]+", word):
        return

    point = await bot_control.get_raw_current_markup()
    point.eng = word
    point.prompt = (f'Enter the word(s)`s or phrase`s for translate {Emoji.OPEN_BOOK}\n\n'
                    f'Format: "word" OR "some phrase, another phrase" OR "word, synonym\n'
                    f'Max translate word or phrase length is {ENG_LENGTH} symbols"\n')
    point.state = States.input_text_new_rus_word
    await bot_control.dream(await point.update())


@commands_router.message(StateFilter(States.input_text_new_rus_word), F.text)
async def accept_input_translate(message: Message, bot_control: BotControl):
    translate = message.text
    await message.delete()

    if len(translate) > ENG_LENGTH or not re.fullmatch(r"[а-яА-Я-, ]+", translate):
        return

    point = await bot_control.get_raw_current_markup()
    Offer().replenish_offer(WordModel(eng=point.eng, translate=translate.strip().lower().split(", ")))
    point.prompt = f'"{point.eng} -> {translate}" sent.\n\nEnter the english word or short phrase: {Emoji.PENCIL}'
    point.state = States.input_text_new_eng_word
    await bot_control.dream(await point.update())
