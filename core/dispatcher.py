import os
from typing import Type, List

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats

from core import MessageConstructor, PrivateStorage, BotCommands, Scavenger
from core.handlers.abyss import abyss_router
from core.handlers.commands import default_commands_router
from core.middleware import BuildBotControl


class BuildBot:
    dispatcher = Dispatcher(
        storage=RedisStorage(
            Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))
        )
    )

    def __init__(
            self,
            *routers,
            token: str,
            private_title_screen: Type[MessageConstructor],
            group_title_screen: Type[MessageConstructor],
            hello_screen: Type[MessageConstructor],
            cache: Type[PrivateStorage]
    ):
        self.bot = Bot(token, default=DefaultBotProperties(parse_mode='HTML'))
        self.dispatcher.update.middleware(BuildBotControl(self.bot, private_title_screen, group_title_screen, hello_screen, cache))
        self.dispatcher.include_routers(default_commands_router, *routers, abyss_router)
        Scavenger.scheduler.start()

    async def start_polling(self, custom_commands: List[BotCommand]):
        commands = BotCommands.commands()
        commands.extend(custom_commands)
        await self.bot.set_my_commands(commands)
        await self.dispatcher.start_polling(self.bot)
