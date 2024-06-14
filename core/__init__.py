import os
from typing import Type
from datetime import datetime, timedelta, UTC

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMediaAudio, Message, CallbackQuery, BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from config import AWAIT_TIME_MESSAGE_DELETE
from core.markups.text_messages import Info
from core.redis import ChatStorage, MessagesPool, PrivateStorage
from core.markups import TextMessageConstructor, PhotoMessageConstructor, VoiceMessageConstructor, \
    MessageConstructor, ButtonWidget, TextWidget

from core.tools.emoji import Emoji
from core.tools.loggers import errors, info


class BotCommands:
    start = Command("start")
    exit = Command("exit")

    @classmethod
    def commands(cls):
        return [
            BotCommand(
                command=f"/start", description=f"Продолжить {Emoji.ZAP}"
            ),
            BotCommand(
                command="/exit", description=f"Закрыть {Emoji.ZZZ}"
            ),
        ]


class _MessagePrivateFilter:
    def __call__(self, message: Message):
        return message.chat.type == "private"


class _CallbackPrivateFilter:
    def __call__(self, callback: CallbackQuery):
        return callback.message.chat.type == "private"


class _MessageGroupFilter:
    def __call__(self, message: Message):
        return message.chat.type == "supergroup"


class _CallbackGroupFilter:
    def __call__(self, callback: CallbackQuery):
        return callback.message.chat.type == "supergroup"


class Routers:
    @staticmethod
    def group():
        router = Router()
        router.message.filter(_MessageGroupFilter())
        router.callback_query.filter(_CallbackGroupFilter())
        return router

    @staticmethod
    def private():
        router = Router()
        router.message.filter(_MessagePrivateFilter())
        router.callback_query.filter(_CallbackPrivateFilter())
        return router


class Scavenger:
    scheduler = AsyncIOScheduler()
    scheduler.configure(jobstore={"default": RedisJobStore(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))}, job_defaults={"coalesce": False})

    def __init__(self, bot_control: "BotControl"):
        self._bot_control = bot_control

    async def add_target(self, message_id: int, await_time: int = AWAIT_TIME_MESSAGE_DELETE):
        run_date = datetime.now() + timedelta(minutes=await_time)
        self.scheduler.add_job(
            self._delete_message,
            id=str(message_id) + self._bot_control.chat_id,
            replace_existing=True,
            args=(message_id,),
            trigger="date",
            run_date=run_date,
        )

    async def _delete_message(self, message_id: int):
        await self._bot_control.delete_message(
            message_id
        )


class BotControl:
    def __init__(
            self,
            bot: Bot,
            chat_id: str,
            state: FSMContext,
            private_title_screen: Type[MessageConstructor],
            group_title_screen: Type[MessageConstructor],
    ):
        self.chat_id = chat_id
        self._state = state
        self._chat_storage = ChatStorage(self.chat_id)
        self.name = self._chat_storage.name
        self._messages_pool = MessagesPool(chat_id)
        self._bot = bot
        self._private_title_screen = private_title_screen
        self._group_title_screen = group_title_screen

    async def set_context(
            self, initializer: Type[MessageConstructor], *args, auto_return: bool = True, **kwargs
    ):
        self._chat_storage.context = initializer, args, kwargs
        if auto_return:
            await self.return_to_context()

    async def create_text_message(self, text_message_constructor: Type[TextMessageConstructor], *args, **kwargs):
        markup = text_message_constructor(*args, **kwargs)
        await markup.init()

        if self._state is not None:
            await self._state.set_state(markup.state)

        try:
            message = await self._bot.send_message(
                chat_id=self.chat_id,
                text=markup.text,
                reply_markup=markup.keyboard,
            )
            await Scavenger(self).add_target(message_id=message.message_id)
            self._messages_pool.add_message_id_to_the_chat_pull(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)

    async def update_text_message(
            self,
            text_message_constructor: Type[TextMessageConstructor], *args, **kwargs
    ):
        markup = text_message_constructor(*args, **kwargs)
        await markup.init()
        if self._state is not None:
            await self._state.set_state(markup.state)

        await self._contextualize_chat()

        last_message_id = self._messages_pool.last_message_id_from_the_chat
        if last_message_id is None:
            await self.create_text_message(text_message_constructor, *args, **kwargs)
            return

        try:
            await self._bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=last_message_id,
                text=markup.text,
                reply_markup=markup.keyboard,
            )
        except TelegramBadRequest:
            await self.delete_message(last_message_id)
            await self.update_text_message(text_message_constructor, *args, **kwargs)

    async def create_photo_message(self, photo_message_constructor: Type[PhotoMessageConstructor], *args, **kwargs):
        markup = photo_message_constructor(*args, **kwargs)
        await markup.init()

        if self._state is not None:
            await self._state.set_state(markup.state)

        await self._contextualize_chat()

        try:
            message = await self._bot.send_photo(
                chat_id=self.chat_id,
                photo=markup.photo,
                caption=markup.text,
                reply_markup=markup.keyboard,
            )
            await Scavenger(self).add_target(message_id=message.message_id)
            self._messages_pool.add_message_id_to_the_chat_pull(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)

    async def update_photo_message(self, photo_message_constructor: Type[PhotoMessageConstructor], *args, **kwargs):
        markup = photo_message_constructor(*args, **kwargs)
        await markup.init()
        if self._state is not None:
            await self._state.set_state(markup.state)

        await self._contextualize_chat()

        last_message_id = self._messages_pool.last_message_id_from_the_chat
        if last_message_id is None:
            await self.create_photo_message(photo_message_constructor, *args, **kwargs)
            return

        try:
            await self._bot.edit_message_media(
                chat_id=self.chat_id,
                message_id=last_message_id,
                media=InputMediaPhoto(media=markup.photo),
            )
            await self._bot.edit_message_caption(
                chat_id=self.chat_id,
                message_id=last_message_id,
                caption=markup.text,
                reply_markup=markup.keyboard
            )
        except TelegramBadRequest:
            await self.delete_message(last_message_id)
            await self.update_photo_message(photo_message_constructor, *args, **kwargs)

    async def create_voice_message(self, voice_message_constructor: Type[VoiceMessageConstructor], *args, **kwargs):
        markup = voice_message_constructor(*args, **kwargs)
        await markup.init()

        if self._state is not None:
            await self._state.set_state(markup.state)

        await self._contextualize_chat()

        try:
            message = await self._bot.send_voice(
                chat_id=self.chat_id,
                voice=markup.voice,
                caption=markup.text,
                reply_markup=markup.keyboard
            )
            await Scavenger(self).add_target(message_id=message.message_id)
            self._messages_pool.add_message_id_to_the_chat_pull(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)

    async def update_voice_message(self, voice_message_constructor: Type[VoiceMessageConstructor], *args, **kwargs):
        markup = voice_message_constructor(*args, **kwargs)
        await markup.init()

        if self._state is not None:
            await self._state.set_state(markup.state)

        await self._contextualize_chat()

        last_message_id = self._messages_pool.last_message_id_from_the_chat
        if last_message_id is None:
            await self.create_voice_message(voice_message_constructor, *args, **kwargs)
            return

        try:
            await self._bot.edit_message_media(
                chat_id=self.chat_id,
                message_id=last_message_id,
                media=InputMediaAudio(media=markup.voice),
                reply_markup=markup.keyboard,
            )
        except (TelegramBadRequest, TelegramNetworkError):
            await self.delete_message(last_message_id)
            await self.update_voice_message(voice_message_constructor, *args, **kwargs)

    async def return_to_context(self):
        try:
            initializer, args, kwargs = self._chat_storage.context
            if TextMessageConstructor in initializer.__bases__:
                await self.update_text_message(
                    initializer, *args, **kwargs
                )
            elif PhotoMessageConstructor in initializer.__bases__:
                await self.update_photo_message(
                    initializer, *args, **kwargs
                )
            elif VoiceMessageConstructor in initializer.__bases__:
                await self.update_voice_message(
                    initializer, *args, **kwargs
                )
            else:
                errors.critical(
                    f"Incorrect initializer in return to context.\n"
                    f"Initializer: {initializer}\n"
                    f"Args: {args}"
                    f"Kwargs: {kwargs}"
                )
                raise ValueError
        except (AttributeError, ValueError, ModuleNotFoundError, BaseException):
            errors.error(f"broken contex", exc_info=True)
            await self.reset_context()

    async def reset_context(self):
        if self.chat_id.startswith("-"):
            await self.set_context(self._group_title_screen)
        else:
            await self.set_context(self._private_title_screen)

    async def _contextualize_chat(self):
        for chat_message_id in self._messages_pool.chat_messages_ids_pull[:-1]:
            await self.delete_message(chat_message_id)

    async def delete_message(self, message_id: int):
        try:
            await self._bot.delete_message(self.chat_id, message_id)
        except TelegramBadRequest:
            pass
        self._messages_pool.remove_message_id_form_the_chat_pull(message_id)

    async def exit(self):
        await self.delete_message(self._messages_pool.last_message_id_from_the_chat)

    async def api_status_code_processing(self, code: int, *expected_codes: int) -> bool:
        if code in expected_codes:
            return True

        if code == 401:
            info.warning(f"Trying unauthorized access. User: {self.chat_id}")
            await self.set_context(self._private_title_screen, self.chat_id)
            await self.update_text_message(
                Info,
                f"Your session expired {Emoji.CRYING_CAT} Please, sign in again {Emoji.DOOR}"
            )

        elif code == 500:
            errors.critical(f"Internal server error.")
            await self.update_text_message(
                Info,
                f"Internal server error {Emoji.CRYING_CAT + Emoji.BROKEN_HEARTH} Sorry"
            )
        else:
            errors.critical(f"Unexpected status from API: {code}")
            await self.update_text_message(
                Info, f"Something broken {Emoji.CRYING_CAT + Emoji.BROKEN_HEARTH} Sorry"
            )
        return False
