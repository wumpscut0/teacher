from typing import Any, Dict, Callable, Awaitable, Type

from aiogram import BaseMiddleware, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Update

from core import BotControl, Info, MessageConstructor
from core.redis import PrivateStorage
from core.tools.emoji import Emoji
from core.tools.loggers import errors


class BuildBotControl(BaseMiddleware):
    def __init__(
            self,
            bot: Bot,
            private_title_screen: Type[MessageConstructor],
            group_title_screen: Type[MessageConstructor],
            hello_screen: Type[MessageConstructor],
            cache: Type[PrivateStorage],
    ):
        self._bot = bot
        self._private_title_screen = private_title_screen
        self._group_title_screen = group_title_screen
        self._hello_screen = hello_screen
        self._cache = cache

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        chat_id = str(await self._extract_chat_id(event))
        bot_control = await self._build_bot_control(event, data["state"], chat_id)
        data["bot_control"] = bot_control
        data["cache"] = self._cache(chat_id)
        data["hello"] = self._hello_screen
        try:
            return await handler(event, data)
        except BaseException as e:
            errors.critical(f"An error occurred when execution some handler", exc_info=True)
            await bot_control.update_text_message(
                Info,
                f"Something went wrong {Emoji.CRYING_CAT + Emoji.BROKEN_HEARTH}"
                f" Sorry"
            )
            raise e

    async def _build_bot_control(self, event, state: FSMContext, chat_id: str):
        bot_control = BotControl(
            self._bot,
            chat_id,
            state,
            self._private_title_screen,
            self._group_title_screen,
        )
        bot_control._chat_storage.name = await self._extract_first_name(event)
        return bot_control

    @classmethod
    async def _extract_chat_id(cls, event: Update):
        try:
            chat_id = event.message.chat.id
        except AttributeError:
            chat_id = event.callback_query.message.chat.id
        return chat_id

    @classmethod
    async def _extract_first_name(cls, event: Update):
        await cls._extract_chat_id(event)
        try:
            first_name = event.message.from_user.full_name
        except AttributeError:
            first_name = event.callback_query.from_user.full_name
        return first_name
