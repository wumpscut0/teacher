from typing import Any, Dict, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Update

from alt_aiogram import BotControl, ChatStorage, Info
from tools.emoji import Emoji
from tools.loggers import errors


class BuildBotControl(BaseMiddleware):
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
        except BaseException as e:
            errors.critical(f"An error occurred when execution some handler", exc_info=True)
            await bot_control.update_text_message(
                Info,
                f"Something went wrong {Emoji.CRYING_CAT + Emoji.BROKEN_HEARTH}"
                f" Sorry"
            )
            raise e

    @classmethod
    async def _build_bot_control(cls, event, state: FSMContext):
        chat_id = await cls._extract_chat_id(event)
        bot_control = BotControl(str(chat_id), state)
        user_storage = ChatStorage(str(chat_id))
        user_storage.name = await cls._extract_first_name(event)
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
