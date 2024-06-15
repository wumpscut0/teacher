import os
from datetime import datetime, timedelta

from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InputMediaAudio, Message, CallbackQuery, BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from config import AWAIT_TIME_MESSAGE_DELETE
from core.markups.text_messages import Info
from core.redis import ContextStorage, ContextStorage, UserStorage, TitleScreens
from core.markups import TextMessageConstructor, PhotoTextMessageConstructor, VoiceTextMessageConstructor, \
    TextMessageConstructor, ButtonWidget, TextWidget

from core.tools.emoji import Emoji
from core.tools.loggers import errors, info


class ImpossibleRestoreContext(BaseException):
    def __str__(self):
        return "Impossible restore context"


class ImpossibleCreateMessage(BaseException):
    def __str__(self):
        return "Impossible create message"


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
            user_storage: UserStorage,
            title_screens: TitleScreens
    ):
        self.chat_id = chat_id
        self.user_storage = user_storage
        self.title_screens = title_screens
        self._context_storage = ContextStorage(self.chat_id, bot.id)
        self._state = state
        self._bot = bot

    async def _actualize_markup(self, raw_markup: TextMessageConstructor):
        await raw_markup.init()
        await self._state.set_state(raw_markup.state)

    async def dig(self, *markups_: TextMessageConstructor):
        await self._look_around(self._context_storage.dig(*markups_))

    async def dig_the_other_way(self, markup: TextMessageConstructor):
        await self._look_around(self._context_storage.dig(markup), dig_straight=False)

    async def dream(self, markup):
        await self._look_around(await self._context_storage.dream(markup))

    async def bury(self):
        await self._look_around(self._context_storage.bury())

    async def look_around(self):
        await self._look_around(self._context_storage.look_around)

    async def sleep(self):
        for message_id in self._context_storage.chat_messages_ids_pull:
            await self._delete_message(message_id)

    async def _create_text_message(self, markup: TextMessageConstructor):
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
            raise ImpossibleCreateMessage

    async def _update_text_message(self, markup: TextMessageConstructor):
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
        except TelegramBadRequest:
            await self._delete_message(last_message_id)
            await self._update_text_message(markup)

    async def _create_photo_message(self, markup: PhotoTextMessageConstructor):
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
            raise ImpossibleCreateMessage

    async def _update_photo_message(self, markup: PhotoTextMessageConstructor):
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
        except TelegramBadRequest:
            await self._delete_message(last_message_id)
            await self._update_photo_message(markup)

    async def _create_voice_message(self, markup: VoiceTextMessageConstructor):
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
            raise ImpossibleCreateMessage

    async def _update_voice_message(self, markup: VoiceTextMessageConstructor):
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
        except (TelegramBadRequest, TelegramNetworkError):
            await self._delete_message(last_message_id)
            await self._update_voice_message(markup)

    async def _look_around(self, markup: TextMessageConstructor, dig_straight=True, _after_reset=False):
        if not _after_reset:
            await self._contextualize_chat()
            await self._actualize_markup(markup)
        try:
            if isinstance(markup, TextMessageConstructor):
                if dig_straight:
                    await self._update_text_message(markup)
                else:
                    await self._create_text_message(markup)
            elif isinstance(markup, PhotoTextMessageConstructor):
                if dig_straight:
                    await self._update_photo_message(markup)
                else:
                    await self._create_photo_message(markup)
            elif isinstance(markup, VoiceTextMessageConstructor):
                if dig_straight:
                    await self._update_voice_message(markup)
                else:
                    await self._create_voice_message(markup)
            else:
                errors.critical(
                    f"Incorrect markup instance.\n"
                    f"Markup: {markup}"
                )
                raise ValueError
        except (AttributeError, ValueError, ModuleNotFoundError, BaseException):
            if _after_reset:
                errors.critical("Impossible restore context", exc_info=True)
                raise ImpossibleRestoreContext
            info.warning(f"broken contex", exc_info=True)
            await self._come_out()

    async def _come_out(self):
        if self.chat_id.startswith("-"):
            markup = self.title_screens.group_title_screen
        else:
            markup = self.title_screens.private_title_screen
        await self._actualize_markup(markup)
        await self._look_around(markup, _after_reset=True)

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
