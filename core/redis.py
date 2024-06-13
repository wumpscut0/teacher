import os
import pickle
from typing import Union, Any, Dict, Tuple

from dotenv import find_dotenv, load_dotenv
from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, ExpiryT, AbsExpiryT

from core.markups import MessageConstructor

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
        result = super().get(name)
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
        result = super().getex(name, ex, px, exat, pxat, persist)
        if result is not None:
            return pickle.loads(result)


STORAGE = CustomRedis(
        host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), db=1
    )


class PrivateStorage:
    def __init__(self, chat_id: str):
        self._chat_id = chat_id


class ChatStorage(PrivateStorage):
    @property
    def name(self):
        return STORAGE.get(f"name:{self._chat_id}")

    @name.setter
    def name(self, data: Any):
        STORAGE.set(f"name:{self._chat_id}", data)

    @property
    def context(self):
        return STORAGE.get(f"context:{self._chat_id}")

    @context.setter
    def context(self, context: Tuple[MessageConstructor, Tuple[Any, ...], Dict[str, Any]]):
        STORAGE.set(f"context:{self._chat_id}", context)


class MessagesPool(PrivateStorage):
    @property
    def chat_messages_ids_pull(self):
        pull = STORAGE.get(f"chat_messages_ids_pull:{self._chat_id}")
        if pull is None:
            return []
        return pull

    @property
    def last_message_id_from_the_chat(self):
        try:
            return self.chat_messages_ids_pull[-1]
        except IndexError:
            pass

    def add_message_id_to_the_chat_pull(self, message_id: int):
        pull = self.chat_messages_ids_pull
        pull.append(message_id)
        self.chat_messages_ids_pull = pull

    def pop_last_message_id_from_the_chat_pull(self):
        pull = self.chat_messages_ids_pull
        try:
            pull.pop()
            self.chat_messages_ids_pull = pull
        except IndexError:
            pass

    def remove_message_id_form_the_chat_pull(self, message_id: int):
        pull = self.chat_messages_ids_pull
        try:
            pull.remove(message_id)
            self.chat_messages_ids_pull = pull
        except ValueError:
            pass

    @chat_messages_ids_pull.setter
    def chat_messages_ids_pull(self, data: Any):
        STORAGE.set(f"chat_messages_ids_pull:{self._chat_id}", data)
