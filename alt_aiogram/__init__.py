import os
from typing import Type
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, InputMediaPhoto, InputMediaAudio, FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from alt_aiogram.markups.text_messages import Info
from alt_aiogram.redis import ChatStorage, MessagesPool, Tuurngaid, OfferStorage
from alt_aiogram.markups.core import TextMessageConstructor, PhotoMessageConstructor, VoiceMessageConstructor, \
    MessageConstructor, ButtonWidget, TextWidget

from tools.emoji import Emoji
from tools.loggers import errors, info


class PrivateTitleScreen(TextMessageConstructor):
    def __init__(self):
        super().__init__()

    async def init(self):
        keyboard_map = [
            [
                ButtonWidget(text="Run English", callback_data="run_english")
            ]
        ]
        self.keyboard_map = keyboard_map


class GroupTitleScreen(VoiceMessageConstructor):
    def __init__(self):
        super().__init__()

    async def init(self):
        self.voice = FSInputFile(os.path.join(os.path.dirname(__file__), "i_obey_you.ogg"))
        keyboard_map = [
            [
                ButtonWidget(text="Get offer", callback_data="get_offer")
            ],
            [
                ButtonWidget(text="Tuurngaid, you can go", callback_data="exit")
            ]
        ]
        self.keyboard_map = keyboard_map


class Scavenger:
    scheduler = AsyncIOScheduler()
    scheduler.configure(jobstore={"default": RedisJobStore(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")))}, job_defaults={"coalesce": False})

    @classmethod
    async def add_target(cls, chat_id: str, message_id: int, await_time: int = 60):
        """
        :param message_id: message for delete
        :param chat_id: telegram chat
        :param await_time: minutes
        :return:
        """
        cls.scheduler.add_job(
            cls._delete_message,
            args=(chat_id, message_id),
            trigger="date",
            next_run_time=datetime.now() + timedelta(minutes=await_time)
        )

    @classmethod
    async def _delete_message(cls, chat_id: str, message_id: int):
        await BotControl(str(chat_id)).delete_message(
            message_id
        )


class BotCommands:
    bot_commands = [
        BotCommand(
            command="/start", description=f"Продолжить {Emoji.ZAP}"
        ),
        BotCommand(
            command="/exit", description=f"Закрыть {Emoji.ZZZ}"
        ),
        BotCommand(
            command="/offer_word", description=f"Предложить новое слово"
        )
    ]

    @classmethod
    def start(cls):
        return Command(cls.bot_commands[0].command.lstrip("/"))

    @classmethod
    def exit(cls):
        return Command(cls.bot_commands[1].command.lstrip("/"))

    @classmethod
    def offer_word(cls):
        return Command(cls.bot_commands[2].command.lstrip("/"))


class BotControl:
    bot = Bot(os.getenv("TOKEN"), default=DefaultBotProperties(parse_mode='HTML'))

    def __init__(
            self, chat_id: str, state: FSMContext | None = None, contextualize: bool = True
    ):
        self._chat_id = chat_id
        self._state = state
        self.contextualize = contextualize
        self.chat_storage = ChatStorage(chat_id)
        self._messages_pool = MessagesPool(chat_id)
        self.tuurngaid = Tuurngaid(chat_id)
        self.offer_storage = OfferStorage()

    @property
    def chat_id(self):
        return str(self._chat_id)

    async def set_context(
            self, initializer: type[MessageConstructor], *args, auto_return: bool = True, **kwargs
    ):
        self.chat_storage.context = initializer, args, kwargs
        if auto_return:
            await self.return_to_context()

    async def create_text_message(self, text_message_constructor: Type[TextMessageConstructor], *args, **kwargs):
        markup = text_message_constructor(*args, **kwargs)
        await markup.init()

        if self._state is not None:
            await self._state.set_state(markup.state)

        try:
            message = await self.bot.send_message(
                chat_id=self._chat_id,
                text=markup.text,
                reply_markup=markup.keyboard,
            )
            await Scavenger.add_target(chat_id=self._chat_id, message_id=message.message_id)
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

        if self.contextualize:
            #  It removes all older message from bot and shift context markup in last message.
            await self._contextualize_chat()

        last_message_id = self._messages_pool.last_message_id_from_the_chat
        if last_message_id is None:
            await self.create_text_message(text_message_constructor, *args, **kwargs)
            return

        try:
            await self.bot.edit_message_text(
                chat_id=self._chat_id,
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

        if self.contextualize:
            #  It removes all older message from bot and shift context markup in last message.
            await self._contextualize_chat()
        try:
            message = await self.bot.send_photo(
                chat_id=self._chat_id,
                photo=markup.photo,
                caption=markup.text,
                reply_markup=markup.keyboard,
            )
            await Scavenger.add_target(chat_id=self._chat_id, message_id=message.message_id, await_time=1)
            self._messages_pool.add_message_id_to_the_chat_pull(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)

    async def update_photo_message(self, photo_message_constructor: Type[PhotoMessageConstructor], *args, **kwargs):
        markup = photo_message_constructor(*args, **kwargs)
        await markup.init()

        if self._state is not None:
            await self._state.set_state(markup.state)

        if self.contextualize:
            #  It removes all older message from bot and shift context markup in last message.
            await self._contextualize_chat()

        last_message_id = self._messages_pool.last_message_id_from_the_chat
        if last_message_id is None:
            await self.create_photo_message(photo_message_constructor, *args, **kwargs)
            return

        try:
            await self.bot.edit_message_media(
                chat_id=self._chat_id,
                message_id=last_message_id,
                media=InputMediaPhoto(media=markup.photo),
            )
            await self.bot.edit_message_caption(
                chat_id=self._chat_id,
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

        if self.contextualize:
            #  It removes all older message from bot and shift context markup in last message.
            await self._contextualize_chat()

        try:
            message = await self.bot.send_voice(
                chat_id=self._chat_id,
                voice=markup.voice,
                caption=markup.text,
                reply_markup=markup.keyboard
            )
            await Scavenger.add_target(chat_id=self._chat_id, message_id=message.message_id)
            self._messages_pool.add_message_id_to_the_chat_pull(message.message_id)
        except TelegramBadRequest:
            errors.critical("Unsuccessfully creating text message.", exc_info=True)

    async def update_voice_message(self, voice_message_constructor: Type[VoiceMessageConstructor], *args, **kwargs):
        markup = voice_message_constructor(*args, **kwargs)
        await markup.init()

        if self._state is not None:
            await self._state.set_state(markup.state)

        if self.contextualize:
            #  It removes all older message from bot and shift context markup in last message.
            await self._contextualize_chat()

        last_message_id = self._messages_pool.last_message_id_from_the_chat
        if last_message_id is None:
            await self.create_voice_message(voice_message_constructor, *args, **kwargs)
            return

        try:
            await self.bot.edit_message_media(
                chat_id=self._chat_id,
                message_id=last_message_id,
                media=InputMediaAudio(media=markup.voice),
                reply_markup=markup.keyboard,
            )
        except (TelegramBadRequest, TelegramNetworkError):
            await self.delete_message(last_message_id)
            await self.update_voice_message(voice_message_constructor, *args, **kwargs)

    async def return_to_context(self):
        try:
            initializer, args, kwargs = self.chat_storage.context
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
            errors.warning(f"broken contex", exc_info=True)
            if self.chat_id.startswith("-"):
                await self.set_context(GroupTitleScreen)
            else:
                await self.set_context(PrivateTitleScreen)

    async def _contextualize_chat(self):
        for chat_message_id in self._messages_pool.chat_messages_ids_pull[:-1]:
            await self.delete_message(chat_message_id)

    async def delete_message(self, message_id: int):
        try:
            await self.bot.delete_message(self._chat_id, message_id)
        except TelegramBadRequest:
            pass
        self._messages_pool.remove_message_id_form_the_chat_pull(message_id)

    async def api_status_code_processing(self, code: int, *expected_codes: int) -> bool:
        if code in expected_codes:
            return True

        if code == 401:
            info.warning(f"Trying unauthorized access. User: {self.chat_id}")
            await self.set_context(PrivateTitleScreen, self.chat_id)
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
