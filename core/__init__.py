import os
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
from core.objects import _SetUpWindows, _UsersIds, _MessagesIds

from tools import ImmuneList, Emoji


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


class BotControl(ImmuneList):
    def __init__(
            self,
            bot: Bot,
            chat_id: str,
            state: FSMContext,
            set_up_windows: _SetUpWindows,
            user_id: str | int | None = None,
            name: str | None = None
    ):
        super().__init__(f"{chat_id}:{bot.id}:context_stack")
        self.chat_id = chat_id
        self.user_id = user_id
        self.name = name
        self.user_uds = _UsersIds(bot.id)
        self._set_up_windows = set_up_windows
        self._messages_storage = _MessagesIds(self.chat_id, bot.id)
        self._state = state
        self._bot = bot
        self._update_message = {
            "text": self._update_text_message,
            "photo": self._update_photo_message,
            "voice": self._update_voice_message,
        }

    async def greetings(self):
        await self.append(await self._set_up_windows["greetings"].update())
        await self.push()

    async def extend(self, *markups_: WindowBuilder):
        names = [i.__class__.__name__ for i in self._list]
        to_extend = []
        for markup in markups_:
            if markup.unique and markup.__class__.__name__ in names:
                continue
            to_extend.append(markup)
        super().extend(to_extend)
        await self.push()

    async def append(self, markup: WindowBuilder):
        if markup.unique and markup.__class__.__name__ in (i.__class__.__name__ for i in self._list):
            await self.push()
        else:
            super().append(markup)
            await self.push()

    async def pop_last(self):
        super().pop_last()
        await self.push()

    async def reset(self, markup: WindowBuilder = None):
        if markup is None:
            if self.chat_id.startswith("-"):
                markup = await self._set_up_windows["group_title_screen"].update()
            else:
                markup = await self._set_up_windows["private_title_screen"].update()
        super().reset(markup)
        for message_id in self._messages_storage._list:
            await self._delete_message(message_id)
        self._messages_storage.destroy()
        await self.push()

    def __getitem__(self, index: int):
        raise SyntaxError

    def __setitem__(self, key, value):
        raise SyntaxError

    @property
    def current(self):
        """
        :return: last added window builder without text_map and keyboard_map
        """
        try:
            markup = self._list[-1]
        except IndexError:
            return
        markup.reset()
        return markup

    async def set_current(self, markup: WindowBuilder):
        try:
            list_ = self._list
            list_[-1] = markup
            self._list = list_
        except IndexError:
            await self.reset(markup)
        await self.push()

    async def _create_text_message(self, markup: WindowBuilder):
        try:
            message = await self._bot.send_message(
                chat_id=self.chat_id,
                text=markup.text,
                reply_markup=markup.keyboard,
            )
            await self._delete_task_message(message_id=message.message_id)
            self._messages_storage.append(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_text_message(self, markup: WindowBuilder):
        last_message_id = self._messages_storage[-1]
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
                await self.extend(markup)
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
            self._messages_storage.append(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_photo_message(self, markup: WindowBuilder):
        last_message_id = self._messages_storage[-1]
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
                await self.extend(markup)
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
            self._messages_storage.append(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)
            raise ValueError("Impossible create message")

    async def _update_voice_message(self, markup: WindowBuilder):
        last_message_id = self._messages_storage[-1]
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
                await self.extend(markup)
            else:
                await self._update_message[markup.type](markup)

    async def push(self, force=False):
        try:
            markup = self._list[-1]
        except IndexError:
            await self.reset()
            return

        await self.clear_chat(force)
        await self._state.set_state(markup.state)
        if not markup.control_inited:
            markup.init_control()
        try:
            await self._update_message[markup.type](markup)
        except (AttributeError, ValueError, ModuleNotFoundError, BaseException):
            if self._set_up_windows["group_title_screen"].__class__.__name__ == markup.__class__.__name__ or self._set_up_windows["private_title_screen"].__class__.__name__ == markup.__class__.__name__:
                errors.critical("Impossible restore context", exc_info=True)
                raise ValueError("Impossible restore context")
            errors.error(f"broken contex", exc_info=True)
            await self.set_current(await Info(f"Something broken {Emoji.BROKEN_HEARTH} Sorry").update())

    async def clear_chat(self, force: bool = False):
        if force:
            messages_ids = self._messages_storage._list
        else:
            messages_ids = self._messages_storage._list[:-1]
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
        self._messages_storage.remove(message_id)

    async def _delete_task_message(self, message_id: int, await_time: int = AWAIT_TIME_MESSAGE_DELETE):
        SCHEDULER.add_job(
            self._delete_message,
            id=str(message_id) + self.chat_id,
            replace_existing=True,
            args=(message_id,),
            trigger="date",
            run_date=datetime.now() + timedelta(minutes=await_time),
        )
