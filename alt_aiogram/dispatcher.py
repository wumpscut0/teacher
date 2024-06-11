import os

from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import CallbackQuery, Message

from alt_aiogram.abyss import abyss_router
from alt_aiogram.middleware import BuildBotControl


# class MessagePrivateFilter:
#     def __call__(self, message: Message):
#         return message.chat.type == "private"
#
#
# class CallbackPrivateFilter:
#     def __call__(self, callback: CallbackQuery):
#         return callback.message.chat.type == "private"


dispatcher = Dispatcher(
    storage=RedisStorage(
        Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))
    )
)

dispatcher.update.middleware(BuildBotControl())
# dispatcher.message.filter(MessagePrivateFilter())
# dispatcher.callback_query.filter(CallbackPrivateFilter())
dispatcher.include_routers(
    abyss_router
)
