from typing import Any, Dict, Callable, Awaitable

from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Update

from core import BotControl, WindowBuilder
from core.markups import Info
from core.redis import TitleScreens
from core.tools.emoji import Emoji
from core.tools.loggers import errors


class BuildBotControl(BaseMiddleware):
    def __init__(
            self,
            bot: Bot,
            private_title_screen: WindowBuilder,
            group_title_screen: WindowBuilder,
            hello_screen: WindowBuilder,
    ):
        self._bot = bot
        self._title_screens = TitleScreens(self._bot.id)
        self._title_screens.private_title_screen = private_title_screen
        self._title_screens.group_title_screen = group_title_screen
        self._title_screens.greetings = hello_screen

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        bot_control = await self._build_bot_control(event, data["state"])
        data["bot_control"] = bot_control
        try:
            return await handler(event, data)
        except (ValueError, BaseException) as e:
            errors.critical(f"An error occurred when execution some handler", exc_info=True)
            await bot_control.dream(
                await Info(f"Something went wrong {Emoji.CRYING_CAT + Emoji.BROKEN_HEARTH} Sorry").update(),
            )
            raise e

    async def _build_bot_control(self, event, state: FSMContext):
        bot_control = BotControl(
            self._bot,
            str(await self._extract_chat_id(event)),
            state,
            self._title_screens,
        )
        return bot_control

    @classmethod
    async def _extract_chat_id(cls, event: Update):
        try:
            chat_id = event.message.chat.id
        except AttributeError:
            chat_id = event.callback_query.message.chat.id
        return chat_id

    @classmethod
    async def _extract_user_id(cls, event: Update):
        try:
            user_id = event.message.from_user.id
        except AttributeError:
            user_id = event.callback_query.message.from_user.id
        return user_id

    @classmethod
    async def _extract_first_name(cls, event: Update):
        await cls._extract_chat_id(event)
        try:
            first_name = event.message.from_user.full_name
        except AttributeError:
            first_name = event.callback_query.from_user.full_name
        return first_name
