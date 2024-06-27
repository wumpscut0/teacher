import os
from asyncio import to_thread
from copy import deepcopy
from datetime import datetime, timedelta

from aiogram.filters import Command
from aiogram.types import BotCommand
from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMediaAudio, Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from core.markups import WindowBuilder, WindowBuilder, ButtonWidget, TextWidget, Info
from core.loggers import telegram_alt_errors, telegram_alt_info
from tools import Emoji, ListStorage, DictStorage


class _BotCommands:
    _AWAIT_TIME_MESSAGE_DELETE = 60
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
        job_defaults={"coalesce": False, "misfire_grace_time": None}
    )


class BotControl:
    def __init__(
            self,
            bot: Bot,
            chat_id: str,
            state: FSMContext,
            bot_storage: DictStorage,
            user_storage: DictStorage,
            name: str | None = None,
            message_life_span: int = 60,
    ):
        self.chat_id = chat_id
        self.name = name
        self.user_storage = user_storage
        self.bot_storage = bot_storage
        self._messages_ids = ListStorage(f"{chat_id}:{bot.id}:messages_ids")
        self._context = ListStorage(f"{chat_id}:{bot.id}:context_stack")
        self._state = state
        self._bot = bot
        self._update_message = {
            "text": self._update_text_message,
            "photo": self._update_photo_message,
            "voice": self._update_voice_message,
        }
        self._message_life_span = message_life_span

    async def greetings(self):
        await self.append(await self.bot_storage.get_value_by_key("greetings"))
        await self.push()

    async def extend(self, *markups_: WindowBuilder):
        names = [i.__class__.__name__ for i in await self._context.get()]
        to_extend = []
        for markup in markups_:
            if markup.unique and markup.__class__.__name__ in names:
                continue
            to_extend.append(markup)

        await self._context.extend(to_extend)
        await self.push()

    async def append(self, markup: WindowBuilder):
        if markup.unique and markup.__class__.__name__ in (i.__class__.__name__ for i in await self._context.get()):
            await self.push()
        else:
            await self._context.append(markup)
            await self.push()

    async def back(self):
        await self._context.pop_last()
        await self.push()

    async def reset(self, markup: WindowBuilder = None):
        if markup is None:
            if self.chat_id.startswith("-"):
                markup = await self.bot_storage.get_value_by_key("group_title_screen")
            else:
                markup = await self.bot_storage.get_value_by_key("private_title_screen")

        await self._context.reset(markup)

        for message_id in await self._messages_ids.get():
            await self._delete_message(message_id)

        await self._messages_ids.destroy()

        await self.push()

    async def current(self):
        """
        :return: if not frozen, return last added window builder without text_map and keyboard_map
        """
        markup = await self._context.get_last()
        if markup is None:
            return
        if markup.frozen:
            return markup
        markup.reset()
        return markup

    async def set_current(self, markup: WindowBuilder):
        await self._context.reset_last(markup)
        await self.push()

    async def _create_text_message(self, markup: WindowBuilder):
        try:
            message = await self._bot.send_message(
                chat_id=self.chat_id,
                text=markup.as_html,
                reply_markup=markup.keyboard,
            )
            await self._delete_task_message(message_id=message.message_id)
            await self._messages_ids.append(message.message_id)
        except TelegramBadRequest as e:
            telegram_alt_errors.critical("Unsuccessfully creating text message.", exc_info=True)
            e.add_note("Impossible create message")
            raise e

    async def _update_text_message(self, markup: WindowBuilder):
        last_message_id = (await self._messages_ids.get_last())
        if last_message_id is None:
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
                await self.append(markup)
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
            await self._messages_ids.append(message.message_id)
        except TelegramBadRequest as e:
            telegram_alt_errors.critical("Unsuccessfully creating text message.", exc_info=True)
            e.add_note("Impossible create message")
            raise e

    async def _update_photo_message(self, markup: WindowBuilder):
        last_message_id = (await self._messages_ids.get_last())
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
                caption="" if markup.as_html == "No Data" else markup.as_html,
                reply_markup=markup.keyboard
            )
        except TelegramBadRequest as e:
            await self._delete_message(last_message_id)
            if "not modified" in e.message:
                await self.append(markup)
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
            await self._messages_ids.append(message.message_id)
        except TelegramBadRequest as e:
            telegram_alt_errors.critical("Unsuccessfully creating text message.", exc_info=True)
            e.add_note("Impossible create message")
            raise e

    async def _update_voice_message(self, markup: WindowBuilder):
        last_message_id = (await self._messages_ids.get_last())
        if last_message_id is None:
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
                await self.append(markup)
            else:
                await self._update_message[markup.type](markup)

    async def init_markup(self, markup: WindowBuilder):
        await self._state.set_state(markup.state)
        custom_keyboard_map = deepcopy(markup.keyboard_map)
        markup.keyboard_map = await to_thread(markup.split, markup.buttons_per_line, markup.partitioned_data)
        for row in custom_keyboard_map:
            markup.add_buttons_in_new_row(*row)
        if not markup.pagination_inited:
            markup.init_pagination()
        if not markup.back_inited:
            markup.init_control()

    async def push(self, force=False):
        await self.clear_chat(force)
        try:
            markup = await self._context.get_last()
            if markup is None:
                raise IndexError
            await self.init_markup(markup)
        except (IndexError, AttributeError, Exception):
            telegram_alt_errors.error("Impossible init build window", exc_info=True)
            await self.reset()
            return

        try:
            await self._update_message[markup.type](markup)
        except (AttributeError, ValueError, ModuleNotFoundError, BaseException) as e:
            if (await self.bot_storage.get())["group_title_screen"].__class__.__name__ == markup.__class__.__name__ or (await self.bot_storage.get())["private_title_screen"].__class__.__name__ == markup.__class__.__name__:
                telegram_alt_errors.critical("Impossible restore context", exc_info=True)
                e.add_note("Impossible restore context. May be incorrect setup WindowBuilder")
                raise e
            telegram_alt_errors.error(f"broken contex", exc_info=True)
            await self.set_current(Info(f"Something broken {Emoji.BROKEN_HEARTH} Sorry"))
            raise e

    async def clear_chat(self, force: bool = False):
        if force:
            messages_ids = await self._messages_ids.get()
        else:
            messages_ids = await self._messages_ids.get_all_except_last()

        for chat_message_id in messages_ids:
            await self._delete_message(chat_message_id)

    async def _delete_message(self, message_id: int):
        try:
            await self._bot.delete_message(self.chat_id, message_id)
        except TelegramBadRequest:
            pass
        await self._messages_ids.remove(message_id)

    async def _delete_task_message(self, message_id: int):
        SCHEDULER.add_job(
            self._delete_message,
            id=str(message_id) + self.chat_id,
            replace_existing=True,
            args=(message_id,),
            trigger="date",
            run_date=datetime.now() + timedelta(minutes=self._message_life_span),
        )
