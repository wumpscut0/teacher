import os

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import CallbackQuery, Message

from alt_aiogram.abyss import abyss_router
from alt_aiogram.commands import commands_router
from alt_aiogram.middleware import BuildBotControl
from group_handlers import party_router
from handlers import english_router


class MessagePrivateFilter:
    def __call__(self, message: Message):
        return message.chat.type == "private"


class CallbackPrivateFilter:
    def __call__(self, callback: CallbackQuery):
        return callback.message.chat.type == "private"


class MessageGroupFilter:
    def __call__(self, message: Message):
        return message.chat.type == "supergroup"


class CallbackGroupFilter:
    def __call__(self, callback: CallbackQuery):
        return callback.message.chat.type == "supergroup"


dispatcher = Dispatcher(
    storage=RedisStorage(
        Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))
    )
)

dispatcher.update.middleware(BuildBotControl())

english_router.message.filter(MessagePrivateFilter())
english_router.callback_query.filter(CallbackPrivateFilter())
dispatcher.include_router(english_router)

commands_router.message.filter(MessagePrivateFilter())
commands_router.callback_query.filter(CallbackPrivateFilter())
dispatcher.include_router(commands_router)

party_router.message.filter(MessageGroupFilter())
party_router.callback_query.filter(CallbackGroupFilter())
dispatcher.include_router(party_router)

# abyss_router.message.filter(MessagePrivateFilter())
# abyss_router.callback_query.filter(CallbackPrivateFilter())
dispatcher.include_router(abyss_router)
