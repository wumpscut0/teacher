import os
import pickle
from typing import Union, Any, List

from dotenv import find_dotenv, load_dotenv
from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, ExpiryT, AbsExpiryT

from core import TextMessageConstructor

load_dotenv(find_dotenv())


class CustomRedis(Redis):
    def set(
        self,
        name: KeyT,
        value: Any,
        ex: Union[ExpiryT, None] = None,
        px: Union[ExpiryT, None] = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,
        get: bool = False,
        exat: Union[AbsExpiryT, None] = None,
        pxat: Union[AbsExpiryT, None] = None,
    ) -> ResponseT:
        return super().set(
            name,
            pickle.dumps(value),
            ex,
            px,
            nx,
            xx,
            keepttl,
            get,
            exat,
            pxat,
        )

    def get(self, name: KeyT) -> ResponseT:
        result: Any = super().get(name)
        if result is not None:
            return pickle.loads(result)

    def setex(self, name: KeyT, time: ExpiryT, value: Any) -> ResponseT:
        return super().setex(
            name,
            time,
            pickle.dumps(value),
        )

    def getex(
        self,
        name: KeyT,
        ex: Union[ExpiryT, None] = None,
        px: Union[ExpiryT, None] = None,
        exat: Union[AbsExpiryT, None] = None,
        pxat: Union[AbsExpiryT, None] = None,
        persist: bool = False,
    ) -> ResponseT:
        result: Any = super().getex(name, ex, px, exat, pxat, persist)
        if result is not None:
            return pickle.loads(result)


class Storage:
    STORAGE = CustomRedis(
        host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=1
    )

    def __init__(self, id_: str = ""):
        self._id_ = id_

    def __get(self, key: str, default: Any | None = None):
        value = self.STORAGE.get(f"{key}:{self._id_}")
        if value is None:
            return default
        return value

    def __set(self, key: str, value: Any):
        self.STORAGE.set(f"{key}:{self._id_}", value)


class TitleScreens(Storage):
    def __init__(self, bot_id: str | int):
        super().__init__(bot_id)

    @property
    def private_title_screen(self) -> TextMessageConstructor:
        return self.__get(f"private_title_screen")

    @private_title_screen.setter
    def private_title_screen(self, private_title_screen: TextMessageConstructor):
        self.__set("private_title_screen", private_title_screen)

    @property
    def group_title_screen(self) -> TextMessageConstructor:
        return self.__get(f"group_title_screen")

    @group_title_screen.setter
    def group_title_screen(self, group_title_screen: TextMessageConstructor):
        self.__set("group_title_screen", group_title_screen)

    @property
    def greetings(self) -> TextMessageConstructor:
        return self.__get(f"greetings")

    @greetings.setter
    def greetings(self, greetings: TextMessageConstructor):
        self.__set("greetings", greetings)


class UserStorage(Storage):
    def __init__(self, user_id: str | int):
        super().__init__(user_id)

    @property
    def name(self):
        return self.__get("name", "Unknown")

    @name.setter
    def name(self, data: Any):
        self.__set("name", data)


class ContextStorage(Storage):
    def __init__(self, chat_id: str | int, bot_id: str | int):
        super().__init__(chat_id + bot_id)

    @property
    def _context_stack(self) -> List[TextMessageConstructor]:
        return self.__get(f"context_stack", [])

    @_context_stack.setter
    def _context_stack(self, context_stack):
        self.__set("context_stack", context_stack)

    @property
    def look_around(self):
        stack = self._context_stack
        if not stack:
            return
        return stack[-1]

    def dream(self, markup):
        stack = self._context_stack
        if not stack:
            return
        stack[-1] = markup
        self._context_stack = stack
        return markup

    def dig(self, *markups: TextMessageConstructor):
        stack = self._context_stack
        stack.extend(markups)
        self._context_stack = stack
        return self.look_around

    def bury(self) -> TextMessageConstructor | None:
        stack = self._context_stack
        if not stack:
            return
        markup = stack.pop()
        self._context_stack = stack
        return markup

    def come_out(self, markup: TextMessageConstructor):
        self._context_stack = [markup]

    @property
    def chat_messages_ids_pull(self) -> [int]:
        return self.__get("chat_messages_ids_pull", [])

    @chat_messages_ids_pull.setter
    def chat_messages_ids_pull(self, data: Any):
        self.__set("chat_messages_ids_pull", data)

    @property
    def last_message_id(self) -> int | None:
        pull = self.chat_messages_ids_pull
        if not pull:
            return
        return pull[-1]

    def add_message_id(self, message_id: int):
        pull = self.chat_messages_ids_pull
        pull.append(message_id)
        self.chat_messages_ids_pull = pull

    def pop_message_id(self):
        pull = self.chat_messages_ids_pull
        if pull:
            pull.pop()
            self.chat_messages_ids_pull = pull

    def remove_message_id(self, message_id: int):
        pull = self.chat_messages_ids_pull
        try:
            pull.remove(message_id)
            self.chat_messages_ids_pull = pull
        except ValueError:
            pass
