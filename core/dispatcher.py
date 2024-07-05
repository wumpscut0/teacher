import os
from typing import List, Type

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import BotCommand

from core import WindowBuilder, SCHEDULER, _BotCommands, BotControl
from core.handlers.abyss import abyss_router
from core.handlers.commands import default_commands_router, group_commands
from core.middleware import BuildBotControl
from tools import DictStorage


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
            greetings: WindowBuilder,
            private_title_screen: WindowBuilder,
            group_title_screen: WindowBuilder,
            bot_control_schema: Type[BotControl] = BotControl
    ):
        self.bot = Bot(token, default=DefaultBotProperties(parse_mode='HTML'))
        self.bot_storage = DictStorage(f"{self.bot.id}:bot_storage")
        self.greetings = greetings
        self.private_title_screen = private_title_screen
        self.group_title_screen = group_title_screen
        self.routers = routers
        self.bot_control_schema = bot_control_schema

    async def start_polling(self, custom_commands: List[BotCommand]):
        self.dispatcher.update.middleware(BuildBotControl(
            self.bot,
            self.bot_storage,
            self.greetings,
            self.private_title_screen,
            self.group_title_screen,
            self.bot_control_schema,
        ))
        self.dispatcher.include_routers(default_commands_router, group_commands, *self.routers, abyss_router)

        SCHEDULER.start()

        commands = _BotCommands.commands()
        commands.extend(custom_commands)
        await self.bot.set_my_commands(commands)

        await self.dispatcher.start_polling(self.bot)
