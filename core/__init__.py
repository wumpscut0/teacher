import os
from copy import deepcopy
from datetime import datetime, timedelta

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMediaAudio, Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from config import AWAIT_TIME_MESSAGE_DELETE
from core.markups import WindowBuilder, WindowBuilder, ButtonWidget, TextWidget, Info

from core.loggers import errors, info

from tools import ImmuneList, ImmuneSet

from aiogram.filters import Command
from aiogram.types import BotCommand

from tools import Emoji, ImmuneDict


class _BotCommands:
    start = Command("start")
    exit = Command("exit")
    continue_ = Command("continue")

    @classmethod
    def commands(cls):
        return [
            BotCommand(
                command=f"/continue", description=f"Continue {Emoji.ZAP}"
            ),
            BotCommand(
                command="/exit", description=f"Close {Emoji.ZZZ}"
            ),
            BotCommand(
                command="/start", description=f"Reboot {Emoji.CYCLE}"
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
            set_up_windows: ImmuneDict,
            user_id: str | int | None = None,
            name: str | None = None
    ):
        self.chat_id = chat_id
        self.user_id = user_id
        self.name = name
        self.user_uds = ImmuneSet(f"{bot.id}:user_ids")
        self.user_storage = ImmuneDict(f"{bot.id}{user_id}:user_storage")
        self.bot_storage = ImmuneDict(f"{bot.id}:bot_storage")
        self._chat_storage = ImmuneList(f"{chat_id}:{bot.id}:messages_ids")
        self._windows = ImmuneList(f"{chat_id}:{bot.id}:context_stack")
        self._set_up_windows = set_up_windows
        self._state = state
        self._bot = bot
        self._update_message = {
            "text": self._update_text_message,
            "photo": self._update_photo_message,
            "voice": self._update_voice_message,
        }

    async def greetings(self):
        await self.append(self._set_up_windows["greetings"]())
        await self.push()

    async def extend(self, *markups_: WindowBuilder):
        names = [i.__class__.__name__ for i in self._windows.list]
        to_extend = []
        for markup in markups_:
            if markup.unique and markup.__class__.__name__ in names:
                continue
            to_extend.append(markup)
        self._windows.extend(to_extend)
        await self.push()

    async def append(self, markup: WindowBuilder):
        if markup.unique and markup.__class__.__name__ in (i.__class__.__name__ for i in self._windows.list):
            await self.push()
        else:
            self._windows.append(markup)
            await self.push()

    async def back(self):
        self._windows.pop_last()
        await self.push()

    async def reset(self, markup: WindowBuilder = None):
        if markup is None:
            if self.chat_id.startswith("-"):
                markup = self._set_up_windows["group_title_screen"]
            else:
                markup = self._set_up_windows["private_title_screen"]
        self._windows.reset(markup)
        for message_id in self._chat_storage.list:
            await self._delete_message(message_id)
        self._chat_storage.destroy()
        await self.push()

    @property
    def current(self):
        """
        :return: last added window builder without text_map and keyboard_map
        """
        try:
            markup = self._windows.list[-1]
        except IndexError:
            return
        markup.reset()
        return markup

    async def set_current(self, markup: WindowBuilder):
        try:
            list_ = self._windows.list
            list_[-1] = markup
            self._windows.list = list_
        except IndexError:
            await self.reset(markup)
            return
        await self.push()

    async def _create_text_message(self, markup: WindowBuilder):
        try:
            message = await self._bot.send_message(
                chat_id=self.chat_id,
                text=markup.as_html,
                reply_markup=markup.keyboard,
            )
            await self._delete_task_message(message_id=message.message_id)
            self._chat_storage.append(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_text_message(self, markup: WindowBuilder):
        try:
            last_message_id = self._chat_storage[-1]
        except IndexError:
            await self._create_text_message(markup)
            return

        try:
            await self._bot.edit_message_text(
                chat_id=self.chat_id,
                message_id=last_message_id,
                text=markup.as_html,
                reply_markup=markup.keyboard,
            )
        except TelegramBadRequest as e:
            await self._delete_message(last_message_id)
            if "not modified" in e.message:
                await self.extend(markup)
            else:
                await self._update_message[markup.type](markup)

    async def _create_photo_message(self, markup: WindowBuilder):
        try:
            message = await self._bot.send_photo(
                chat_id=self.chat_id,
                photo=markup.photo,
                caption="" if markup.as_html == "No Data" else markup.as_html,
                reply_markup=markup.keyboard,
            )
            await self._delete_task_message(message_id=message.message_id)
            self._chat_storage.append(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_photo_message(self, markup: WindowBuilder):
        try:
            last_message_id = self._chat_storage[-1]
        except IndexError:
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
                caption="" if markup.as_html == "No Data" else markup.as_html,
                reply_markup=markup.keyboard
            )
        except TelegramBadRequest as e:
            await self._delete_message(last_message_id)
            if "not modified" in e.message:
                await self.extend(markup)
            else:
                await self._update_message[markup.type](markup)

    async def _create_voice_message(self, markup: WindowBuilder):
        try:
            message = await self._bot.send_voice(
                chat_id=self.chat_id,
                voice=markup.voice,
                caption="" if markup.as_html == "No Data" else markup.as_html,
                reply_markup=markup.keyboard
            )
            await self._delete_task_message(message_id=message.message_id)
            self._chat_storage.append(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_voice_message(self, markup: WindowBuilder):
        try:
            last_message_id = self._chat_storage[-1]
        except IndexError:
            await self._create_voice_message(markup)
            return

        try:
            await self._bot.edit_message_media(
                chat_id=self.chat_id,
                message_id=last_message_id,
                media=InputMediaAudio(media=markup.voice),
            )
            await self._bot.edit_message_caption(
                chat_id=self.chat_id,
                message_id=last_message_id,
                caption="" if markup.as_html == "No Data" else markup.as_html,
                reply_markup=markup.keyboard
            )
        except TelegramBadRequest as e:
            await self._delete_message(last_message_id)
            if "not modified" in e.message:
                await self.extend(markup)
            else:
                await self._update_message[markup.type](markup)

    async def init_window(self, markup: WindowBuilder):
        await self._state.set_state(markup.state)
        custom_keyboard_map = deepcopy(markup.keyboard_map)
        markup.keyboard_map = markup.split(markup.buttons_per_line, markup.partitioned_data)
        for row in custom_keyboard_map:
            markup.add_buttons_in_new_row(*row)
        if not markup.inited_pagination:
            markup.init_pagination()
        if not markup.back_inited:
            markup.init_control()

    async def push(self, force=False):
        await self.clear_chat(force)
        try:
            markup = self._windows[-1]
            await self.init_window(markup)
        except (IndexError, AttributeError, Exception):
            errors.error("Impossible init build window", exc_info=True)
            await self.reset()
            return

        try:
            await self._update_message[markup.type](markup)
        except (AttributeError, ValueError, ModuleNotFoundError, BaseException):
            if self._set_up_windows["group_title_screen"].__class__.__name__ == markup.__class__.__name__ or self._set_up_windows["private_title_screen"].__class__.__name__ == markup.__class__.__name__:
                errors.critical("Impossible restore context", exc_info=True)
                raise ValueError("Impossible restore context")
            errors.error(f"broken contex", exc_info=True)
            await self.set_current(Info(f"Something broken {Emoji.BROKEN_HEARTH} Sorry"))

    async def clear_chat(self, force: bool = False):
        if force:
            messages_ids = self._chat_storage.list
        else:
            messages_ids = self._chat_storage.list[:-1]
        for chat_message_id in messages_ids:
            await self._delete_message(chat_message_id)

    async def _delete_message(self, message_id: int):
        if message_id is None:
            info.warning("Trying delete not existing message")
            return
        try:
            await self._bot.delete_message(self.chat_id, message_id)
        except TelegramBadRequest:
            pass
        self._chat_storage.remove(message_id)

    async def _delete_task_message(self, message_id: int, await_time: int = AWAIT_TIME_MESSAGE_DELETE):
        SCHEDULER.add_job(
            self._delete_message,
            id=str(message_id) + self.chat_id,
            replace_existing=True,
            args=(message_id,),
            trigger="date",
            run_date=datetime.now() + timedelta(minutes=await_time),
        )
