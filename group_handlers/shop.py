from aiogram import F
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from FSM import States
from core import BotControl, Routers
from core.markups import Info, WindowBuilder, Input
from group_markups import EditEnglishRun, WordTickCallbackData, AcceptOffer
from tools import Emoji

party_router = Routers.group()


@party_router.callback_query(F.data == "add_content")
async def add_content(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.append(Input("Send photo or audio", state=States.input_photo_audio_add_content))


@party_router.message(StateFilter(States.input_photo_audio_add_content), F.content_type.in_("audio", "photo"))
async def add_content(message: Message, bot_control: BotControl):
    message.photo[0].file_id
    await message.bot.send_photo()
    await bot_control.append(Input("Send photo or audio", state=States.input_photo_audio_add_content))