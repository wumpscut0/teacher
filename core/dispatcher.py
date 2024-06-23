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
from tools import ImmuneDict


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
        set_up_windows = ImmuneDict(self.bot.id)
        set_up_windows["private_title_screen"] = private_title_screen
        set_up_windows["group_title_screen"] = group_title_screen
        set_up_windows["greetings"] = hello_screen
        self.dispatcher.update.middleware(BuildBotControl(
            self.bot,
            set_up_windows
        ))
        self.dispatcher.include_routers(default_commands_router, group_commands, *routers, abyss_router)
        SCHEDULER.start()

    async def start_polling(self, custom_commands: List[BotCommand]):
        commands = _BotCommands.commands()
        commands.extend(custom_commands)
        await self.bot.set_my_commands(commands)
        await self.dispatcher.start_polling(self.bot)
