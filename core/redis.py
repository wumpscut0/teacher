import os
import pickle
from typing import Union, Any, List

from dotenv import find_dotenv, load_dotenv
from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, ExpiryT, AbsExpiryT

from core.tools.loggers import errors

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

    def _get(self, key: str, default: Any | None = None):
        try:
            value = self.STORAGE.get(f"{key}:{self._id_}")
        except (AttributeError, ModuleNotFoundError, Exception):
            errors.error("Impossible restore deserialized data")
            self._set(key, default)
            return default
        if value is None:
            return default
        return value

    def _set(self, key: str, value: Any):
        self.STORAGE.set(f"{key}:{self._id_}", value)


class TitleScreens(Storage):
    def __init__(self, bot_id: str | int):
        super().__init__(bot_id)

    @property
    def private_title_screen(self):
        return self._get(f"private_title_screen")

    @private_title_screen.setter
    def private_title_screen(self, private_title_screen):
        self._set("private_title_screen", private_title_screen)

    @property
    def group_title_screen(self):
        return self._get(f"group_title_screen")

    @group_title_screen.setter
    def group_title_screen(self, group_title_screen):
        self._set("group_title_screen", group_title_screen)

    @property
    def greetings(self):
        return self._get(f"greetings")

    @greetings.setter
    def greetings(self, greetings):
        self._set("greetings", greetings)

    @property
    def users_ids(self):
        return self._get(f"users_ids", [])

    def add_user_id(self, user_id: Any):
        user_ids = self.users_ids
        user_ids.append(user_id)
        self.users_ids = user_ids

    @users_ids.setter
    def users_ids(self, users_ids: List[Any]):
        self._set("users_ids", users_ids)


class ContextStorage(Storage):
    def __init__(self, chat_id: str | int, bot_id: str | int):
        super().__init__(f"{chat_id}{bot_id}")

    @property
    def _context_stack(self) -> List:
        return self._get(f"context_stack", [])

    @_context_stack.setter
    def _context_stack(self, context_stack: List):
        self._set("context_stack", context_stack)

    @property
    def look_around(self):
        stack = self._context_stack
        if not stack:
            return
        return stack[-1]

    def dream(self, markup):
        stack = self._context_stack
        if not stack:
            stack.append(markup)
        else:
            stack[-1] = markup
        self._context_stack = stack
        return markup

    def dig(self, *markups):
        stack = self._context_stack
        names = [i.id for i in stack]
        stack.extend((markup for markup in markups if markup.id not in names))
        self._context_stack = stack
        return self.look_around

    def bury(self):
        stack = self._context_stack
        if not stack:
            return
        stack.pop()
        self._context_stack = stack
        return self.look_around

    def come_out(self, markup):
        self._context_stack = [markup]

    @property
    def chat_messages_ids_pull(self) -> [int]:
        return self._get("chat_messages_ids_pull", [])

    @chat_messages_ids_pull.setter
    def chat_messages_ids_pull(self, data: Any):
        self._set("chat_messages_ids_pull", data)

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
