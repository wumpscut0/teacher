import asyncio
from asyncio import sleep
from copy import deepcopy
from os import getenv
from datetime import datetime, timedelta

from aiogram.filters import Command
from aiogram.types import BotCommand
from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMediaAudio, Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from core.markups import WindowBuilder
from core.loggers import errors_alt_telegram, info_alt_telegram
from tools import Emoji, ListStorage, DictStorage


class _BotCommands:
    _AWAIT_TIME_MESSAGE_DELETE = 60
    start = Command("start")
    exit = Command("exit")

    @classmethod
    def commands(cls):
        return [
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
        jobstore={"default": RedisJobStore(host=getenv("REDIS_HOST"), port=int(getenv("REDIS_PORT")))},
        job_defaults={"coalesce": False, "misfire_grace_time": None}
    )


class BotControl:
    def __init__(
            self,
            *,
            bot: Bot,
            chat_id: str,
            state: FSMContext,
            greetings: WindowBuilder,
            private_title_screen: WindowBuilder,
            group_title_screen: WindowBuilder,
            bot_storage: DictStorage,
            user_storage: DictStorage,
            name: str | None = None,
            message_life_span: int = 60,
    ):
        self.chat_id = chat_id
        self.name = name
        self.user_storage = user_storage
        self.bot_storage = bot_storage
        self._greetings = greetings
        self._private_title_screen = private_title_screen
        self._group_title_screen = group_title_screen
        self._messages_ids = ListStorage(f"{chat_id}:{bot.id}:messages_ids")
        self._context = ListStorage(f"{chat_id}:{bot.id}:context_stack")
        self._state = state
        self._bot = bot
        self._update_message = {
            "text": self._update_text_message,
            "photo": self._update_photo_message,
            "voice": self._update_voice_message,
            "audio": self._update_voice_message
        }
        self._message_life_span = message_life_span
        self._temp_current_markup_name = None

    async def greetings(self):
        await self.append(self._greetings)

    async def append(self, markup: WindowBuilder):
        if self._temp_current_markup_name != markup.__class__.__name__:
            try:
                await markup(self)
            except TypeError:
                pass

        if markup.initializing and await self._update_chat(markup):
            await self._context.append(markup)

    async def back(self, update=False):
        await self.pop_last()
        markup = await self._context.get_last()

        if markup is None:
            await self.reset()
            return

        if update:
            markup.reset()
            try:
                await markup(self)
            except TypeError:
                pass

        await self.set_current(markup, update=False)

    async def pop_last(self):
        return await self._context.pop_last()

    async def refresh(self):
        await self._update_chat(await self._context.get_last())

    async def reset(self):
        await self._context.destroy()
        for message_id in await self._messages_ids.get():
            await self._delete_message(message_id)
        await self._messages_ids.destroy()

        if self.chat_id.startswith("-"):
            markup = deepcopy(self._group_title_screen)
        else:
            markup = deepcopy(self._private_title_screen)

        try:
            await markup(self)
        except TypeError:
            pass

        await self._update_chat(markup)

    async def get_current(self):
        """
        :return: last appended window builder without text_map and keyboard_map
        """
        markup = await self._context.get_last()
        if markup is None:
            return
        markup.reset()
        self._temp_current_markup_name = markup.__class__.__name__
        return markup

    async def set_current(self, markup: WindowBuilder, update=True):
        if update:
            try:
                await markup(self)
            except TypeError:
                pass

        if markup.initializing and await self._update_chat(markup):
            await self._context.set_last(markup)

    async def _create_text_message(self, markup: WindowBuilder):
        message = await self._bot.send_message(
            chat_id=self.chat_id,
            text=markup.as_html,
            reply_markup=markup.keyboard,
        )
        await self._delete_task_message(message_id=message.message_id)
        await self._messages_ids.append(message.message_id)

    async def _update_text_message(self, markup: WindowBuilder):
        last_message_id = (await self._messages_ids.get_last())
        if last_message_id is None:
            await self._create_text_message(markup)
            return True

        await self._bot.edit_message_text(
            chat_id=self.chat_id,
            message_id=last_message_id,
            text=markup.as_html,
            reply_markup=markup.keyboard,
        )
        return True

    async def _create_photo_message(self, markup: WindowBuilder):
        message = await self._bot.send_photo(
            chat_id=self.chat_id,
            photo=markup.photo,
            caption="" if markup.as_html == "No Data" else markup.as_html,
            reply_markup=markup.keyboard,
        )
        await self._delete_task_message(message_id=message.message_id)
        await self._messages_ids.append(message.message_id)

    async def _update_photo_message(self, markup: WindowBuilder):
        last_message_id = (await self._messages_ids.get_last())
        if last_message_id is None:
            await self._create_photo_message(markup)
            return True

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
        return True

    async def _create_voice_message(self, markup: WindowBuilder):
        message = await self._bot.send_voice(
            chat_id=self.chat_id,
            voice=markup.voice,
            caption="" if markup.as_html == "No Data" else markup.as_html,
            reply_markup=markup.keyboard
        )
        await self._delete_task_message(message_id=message.message_id)
        await self._messages_ids.append(message.message_id)

    async def _update_voice_message(self, markup: WindowBuilder):
        last_message_id = await self._messages_ids.get_last()
        if last_message_id is None:
            await self._create_voice_message(markup)
            return True

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
        return True

    async def _update_chat(self, markup: WindowBuilder | None, force=False, attempt=1) -> bool:
        await self.clear_chat(force)
        try:
            if markup is None:
                await self.reset()
            else:
                markup.init()
                await self._state.set_state(markup.state)
                return await self._update_message[markup.type](markup)
        except (IndexError, AttributeError, Exception) as e:
            if "there is no" in e.message:
                await self._delete_message(await self._messages_ids.get_last())
                return await self._update_chat(markup, force)
            if "Flood control" in e.message:
                await sleep(1)
                return await self._update_chat(markup, force)
            elif "not modified" in e.message:
                return False
            elif "Impossible create" in e.message or attempt <= 0:
                raise e
            else:
                errors_alt_telegram.error(f"Impossible build markup", exc_info=True)
                await sleep(1)
                return await self._update_chat(markup, force, attempt - 1)

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
