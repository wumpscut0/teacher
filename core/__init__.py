import os
from datetime import datetime, timedelta
from typing import Any

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMediaAudio, Message, CallbackQuery, BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from config import AWAIT_TIME_MESSAGE_DELETE
from core.redis import ContextStorage, ContextStorage, TitleScreens
from core.markups import WindowBuilder, WindowBuilder, ButtonWidget, TextWidget, Info

from core.tools.emoji import Emoji
from core.tools.loggers import errors, info


class BotCommands:
    start = Command("start")
    exit = Command("exit")
    continue_ = Command("continue")

    @classmethod
    def commands(cls):
        return [
            BotCommand(
                command=f"/continue", description=f"Продолжить {Emoji.ZAP}"
            ),
            BotCommand(
                command="/exit", description=f"Закрыть {Emoji.ZZZ}"
            ),
            BotCommand(
                command="/start", description=f"Перезагрузить {Emoji.CYCLE}"
            )
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


SCHEDULER = AsyncIOScheduler()
SCHEDULER.configure(
        jobstore={"default": RedisJobStore(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))},
        job_defaults={"coalesce": False}
    )


class BotControl:
    def __init__(
            self,
            bot: Bot,
            chat_id: str,
            state: FSMContext,
            title_screens: TitleScreens,
            user_id: str | int | None = None,
            name: str | None = None
    ):
        self.chat_id = chat_id
        self.name = name
        self.user_id = user_id
        self.title_screens = title_screens
        self._context_storage = ContextStorage(self.chat_id, bot.id)
        self._state = state
        self._bot = bot
        self._update_message = {
            "text": self._update_text_message,
            "photo": self._update_photo_message,
            "voice": self._update_voice_message,
        }
        self._create_message = {
            "text": self._create_text_message,
            "photo": self._create_photo_message,
            "voice": self._create_voice_message,
        }

    async def dig(self, *markups_: WindowBuilder):
        await self._look_around(self._context_storage.dig(*markups_))

    async def redirect_dig(self, markup: WindowBuilder):
        await self._look_around(self._context_storage.dig(markup), dig_straight=False)

    async def get_raw_current_markup(self) -> Any:
        """
        :return: last added window builder without text_map and keyboard_map
        """
        point = self._context_storage.look_around
        point.reset()
        return point

    async def dream(self, markup):
        await self._look_around(self._context_storage.dream(markup))

    async def bury(self):
        markup = self._context_storage.bury()
        if markup is None:
            await self._come_out()
        else:
            await self._look_around(markup)

    async def look_around(self):
        markup = self._context_storage.look_around
        if markup is None:
            await self._come_out()
        else:
            await self._look_around(markup)

    async def sleep(self):
        for message_id in self._context_storage.chat_messages_ids_pull:
            await self._delete_message(message_id)

    async def _create_text_message(self, markup: WindowBuilder):
        try:
            message = await self._bot.send_message(
                chat_id=self.chat_id,
                text=markup.text,
                reply_markup=markup.keyboard,
            )
            await self._delete_task_message(message_id=message.message_id)
            self._context_storage.add_message_id(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_text_message(self, markup: WindowBuilder):
        last_message_id = self._context_storage.last_message_id
        if last_message_id is None:
            await self._create_text_message(markup)
            return
        try:
            await self._bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=last_message_id,
                text=markup.text,
                reply_markup=markup.keyboard,
            )
        except TelegramBadRequest as e:
            await self._delete_message(last_message_id)
            if "not modified" in e.message:
                await self.dig(markup)
            else:
                await self._update_message[markup.type](markup)

    async def _create_photo_message(self, markup: WindowBuilder):
        try:
            message = await self._bot.send_photo(
                chat_id=self.chat_id,
                photo=markup.photo,
                caption=markup.text,
                reply_markup=markup.keyboard,
            )
            await self._delete_task_message(message_id=message.message_id)
            self._context_storage.add_message_id(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_photo_message(self, markup: WindowBuilder):
        last_message_id = self._context_storage.last_message_id
        if last_message_id is None:
            await self._create_photo_message(markup)
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
        except TelegramBadRequest as e:
            await self._delete_message(last_message_id)
            if "not modified" in e.message:
                await self.dig(markup)
            else:
                await self._update_message[markup.type](markup)

    async def _create_voice_message(self, markup: WindowBuilder):
        try:
            message = await self._bot.send_voice(
                chat_id=self.chat_id,
                voice=markup.voice,
                caption=markup.text,
                reply_markup=markup.keyboard
            )
            await self._delete_task_message(message_id=message.message_id)
            self._context_storage.add_message_id(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_voice_message(self, markup: WindowBuilder):
        last_message_id = self._context_storage.last_message_id
        if last_message_id is None:
            await self._create_voice_message(markup)
            return

        try:
            await self._bot.edit_message_media(
                chat_id=self.chat_id,
                message_id=last_message_id,
                media=InputMediaAudio(media=markup.voice),
                reply_markup=markup.keyboard,
            )
        except TelegramBadRequest as e:
            await self._delete_message(last_message_id)
            if "not modified" in e.message:
                await self.dig(markup)
            else:
                await self._update_message[markup.type](markup)

    async def _look_around(self, markup: WindowBuilder, dig_straight=True):
        await self._contextualize_chat()
        await self._state.set_state(markup.state)
        if not markup.control_inited:
            markup.init_control()
        try:
            if dig_straight:
                await self._update_message[markup.type](markup)
            else:
                await self._create_message[markup.type](markup)
        except (AttributeError, ValueError, ModuleNotFoundError, BaseException):
            if self.title_screens.group_title_screen.__class__.__name__ == markup.__class__.__name__ or self.title_screens.private_title_screen.__class__.__name__ == markup.__class__.__name__:
                errors.critical("Impossible restore context", exc_info=True)
                raise ValueError("Impossible restore context")
            errors.error(f"broken contex", exc_info=True)

            await self._come_out()

    async def _come_out(self):
        if self.chat_id.startswith("-"):
            markup = await self.title_screens.group_title_screen.update()
        else:
            markup = await self.title_screens.private_title_screen.update()
        self._context_storage.come_out(markup)
        await self.dig(markup)

    async def _contextualize_chat(self):
        for chat_message_id in self._context_storage.chat_messages_ids_pull[:-1]:
            await self._delete_message(chat_message_id)

    async def _delete_message(self, message_id: int):
        if message_id is None:
            info.warning("Trying delete not existing message")
            return
        try:
            await self._bot.delete_message(self.chat_id, message_id)
        except TelegramBadRequest:
            pass
        self._context_storage.remove_message_id(message_id)

    async def _delete_task_message(self, message_id: int, await_time: int = AWAIT_TIME_MESSAGE_DELETE):
        SCHEDULER.add_job(
            self._delete_message,
            id=str(message_id) + self.chat_id,
            replace_existing=True,
            args=(message_id,),
            trigger="date",
            run_date=datetime.now() + timedelta(minutes=await_time),
        )

    async def reset(self):
        for message_id in self._context_storage.chat_messages_ids_pull:
            await self._delete_message(message_id)
        self._context_storage.chat_messages_ids_pull = []
        await self._come_out()

    # async def api_status_code_processing(self, code: int, *expected_codes: int) -> bool:
    #     if code in expected_codes:
    #         return True
    #
    #     if code == 401:
    #         info.warning(f"Trying unauthorized access. User: {self.chat_id}")
    #         await self.set_context(self._private_title_screen, self.chat_id)
    #         await self._update_text_message(
    #             Info,
    #             f"Your session expired {Emoji.CRYING_CAT} Please, sign in again {Emoji.DOOR}"
    #         )
    #
    #     elif code == 500:
    #         errors.critical(f"Internal server error.")
    #         await self._update_text_message(
    #             Info,
    #             f"Internal server error {Emoji.CRYING_CAT + Emoji.BROKEN_HEARTH} Sorry"
    #         )
    #     else:
    #         errors.critical(f"Unexpected status from API: {code}")
    #         await self._update_text_message(
    #             Info, f"Something broken {Emoji.CRYING_CAT + Emoji.BROKEN_HEARTH} Sorry"
    #         )
    #     return False
