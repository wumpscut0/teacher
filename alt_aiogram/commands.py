import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from alt_aiogram import BotCommands, BotControl
from alt_aiogram.FSM import States
from alt_aiogram.markups.text_messages import Input
from database.queries import insert_user
from tools.emoji import Emoji

commands_router = Router()
CONTENT_LENGTH = 100


@commands_router.message(BotCommands.start())
async def start(message: Message, bot_control: BotControl):
    await message.delete()
    await insert_user(bot_control.chat_id)
    await bot_control.return_to_context()


@commands_router.message(BotCommands.exit())
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.delete_message(bot_control._messages_pool.last_message_id_from_the_chat)


@commands_router.message(BotCommands.offer_word())
async def offer_word(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.update_text_message(
        Input,
        f"Enter the english word or short phrase {Emoji.PENCIL}",
        state=States.input_text_new_eng_word
    )


@commands_router.message(StateFilter(States.input_text_new_eng_word), F.text)
async def offer_new_eng_word(message: Message, bot_control: BotControl):
    word = message.text
    await message.delete()

    if len(word) > CONTENT_LENGTH:
        await bot_control.update_text_message(
            Input,
            f"Max english word or phrase length is {CONTENT_LENGTH} symbols",
            state=States.input_text_new_eng_word
        )
        return

    if not re.fullmatch(r"[a-zA-Z ]+", word):
        await bot_control.update_text_message(
            Input,
            f"English word or phrase must contains only ASCII symbols {Emoji.CRYING_CAT}",
            state=States.input_text_new_eng_word
        )
        return

    bot_control.tuurngaid.new_eng_word = word
    await bot_control.update_text_message(
        Input,
        f"Enter the word(s)`s or phrase`s for translate {Emoji.OPEN_BOOK}\n"
        f"For example: some phrase, another phrase OR word, synonym",
        state=States.input_text_new_rus_word
    )


@commands_router.message(StateFilter(States.input_text_new_rus_word), F.text)
async def accept_input_translate(message: Message, bot_control: BotControl):
    word = message.text
    await message.delete()

    if len(word) > CONTENT_LENGTH:
        await bot_control.update_text_message(
            Input,
            f"Max translate word or phrase length is {CONTENT_LENGTH} symbols",
            state=States.input_text_new_rus_word
        )
        return

    bot_control.tuurngaid.replenish_offer(word)
    await bot_control.update_text_message(
        Input,
        f"Enter the english word or short phrase: {Emoji.PENCIL}",
        state=States.input_text_new_eng_word
    )
