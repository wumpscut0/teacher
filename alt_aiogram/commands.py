import re

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message

from alt_aiogram import BotCommands, BotControl
from alt_aiogram.FSM import States
from alt_aiogram.markups.text_messages import Input, Info
from alt_aiogram.redis import Tuurngaid
from database.queries import insert_user
from tools.emoji import Emoji

commands_router = Router()
CONTENT_LENGTH = 100


@commands_router.message(BotCommands.start())
async def start(message: Message, bot_control: BotControl):
    await message.delete()
    await insert_user(bot_control.user_id)
    await bot_control.return_to_context()


@commands_router.message(BotCommands.exit())
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.delete_message(bot_control._messages_pool.last_message_id_from_the_chat)


# @commands_router.message(BotCommands.report())
# async def report(message: Message, bot_control: BotControl):
#     await message.delete()
#     await bot_control.update_text_message(
#         Input, f"О чем вы бы хотели сказать? {Emoji.PENCIL}", state=States.input_text_to_admin
#     )

@commands_router.message(BotCommands.offer_word())
async def offer_word(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.update_text_message(
        Input,
        f"Enter the english word or short phrase: {Emoji.PENCIL}",
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

    if not re.fullmatch(r"[a-zA-Z ]", word):
        await bot_control.update_text_message(
            Input,
            f"English word or phrase must contains only ASCII symbols",
            state=States.input_text_new_eng_word
        )
        return

    bot_control.tuurngaid = word
    await bot_control.update_text_message(
        Input,
        f"Enter the word`s or phrase`s translate",
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

    bot_control.tuurngaid.replenish_dict(word)
    await bot_control.update_text_message(
        Input,
        f"Enter the english word or short phrase: {Emoji.PENCIL}",
        state=States.input_text_new_eng_word
    )
# @commands_router.message(StateFilter(States.input_text_to_admin), F.text)
# async def send_message_to_admin_accept_input(message: Message, bot_control: BotControl):
#     message_ = message.text
#     await message.delete()
#
#     await bot_control.send_message_to_admin(message_)
#     await bot_control.update_text_message(
#         Info, f"Сообщение отправлено {Emoji.INCOMING_ENVELOPE} Спасибо"
#     )


@commands_router.message(F.text == "get offer")
async def offer_word(message: Message, bot_control: BotControl):
    if message.chat.type == "group":
        ...
