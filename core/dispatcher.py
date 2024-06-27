import os
from typing import List

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import BotCommand

from core import WindowBuilder, SCHEDULER, _BotCommands
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
            private_title_screen: WindowBuilder,
            group_title_screen: WindowBuilder,
            hello_screen: WindowBuilder,
    ):
        self.bot = Bot(token, default=DefaultBotProperties(parse_mode='HTML'))
        self.bot_storage = DictStorage(f"{self.bot.id}:bot_storage")
        self._set_up = {
            "private_title_screen": private_title_screen,
            "group_title_screen": group_title_screen,
            "greetings": hello_screen
        }
        self.routers = routers

    async def start_polling(self, custom_commands: List[BotCommand]):
        for k, v in self._set_up.items():
            await self.bot_storage.set_value_by_key(k, v)
        self.dispatcher.update.middleware(BuildBotControl(self.bot, self.bot_storage))
        self.dispatcher.include_routers(default_commands_router, group_commands, *self.routers, abyss_router)

        SCHEDULER.start()

        commands = _BotCommands.commands()
        commands.extend(custom_commands)
        await self.bot.set_my_commands(commands)

        await self.dispatcher.start_polling(self.bot)
