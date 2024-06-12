import os
import pickle
from typing import Union, Any, Dict, Tuple, List

from aiogram.filters.callback_data import CallbackData
from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, ExpiryT, AbsExpiryT

from alt_aiogram.markups.core import MessageConstructor, ButtonWidget
from dotenv import find_dotenv, load_dotenv

from tools import Emoji, split

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


class OfferWordTickCallbackData(CallbackData, prefix="offer_word_tick"):
    index: int


class Tuurngaid(PrivateStorage):
    @property
    def words(self):
        return STORAGE.get(f"words:{self._chat_id}")

    @words.setter
    def words(self, words: List[Tuple[str, str, int | None]]):
        STORAGE.set(f"words:{self._chat_id}", words)

    @property
    def new_eng_word(self):
        return STORAGE.get(f"new_eng_word:{self._chat_id}")

    @new_eng_word.setter
    def new_eng_word(self, new_eng_word: str):
        STORAGE.set(f"new_eng_word:{self._chat_id}", new_eng_word)

    @property
    def word_index(self):
        return STORAGE.get(f"word_index:{self._chat_id}")

    @word_index.setter
    def word_index(self, word_index: int):
        STORAGE.set(f"word_index:{self._chat_id}", word_index)

    def replenish_offer(self, translate: str):
        offer_storage = OfferStorage()
        offer_storage.replenish_offer(f"{self.new_eng_word}:{translate}")


class OfferStorage:
    _size_offer_page = 10

    @property
    def offer(self):
        offer_list = STORAGE.get(f"offer")
        if offer_list is None:
            return []
        return offer_list

    def replenish_offer(self, word: str):
        print(word)
        offer_list = self.offer
        offer_list.append(ButtonWidget(
            text=word,
            callback_data=OfferWordTickCallbackData(index=len(offer_list) - 1),
            mark=Emoji.TICK)
        )
        self.offer = offer_list

    @property
    def offer_page(self):
        page = STORAGE.get(f"offer_page")
        if page is None:
            return 0

    @offer_page.setter
    def offer_page(self, page: int):
        STORAGE.set(f"offer_page", page)

    def flip_left_offer(self):
        STORAGE.set(f"offer_page", (self.offer_page - 1) % len(split(self._size_offer_page, self.offer_copy)))

    def flip_right_offer(self):
        STORAGE.set(f"offer_page", (self.offer_page + 1) % len(split(self._size_offer_page, self.offer_copy)))

    @offer.setter
    def offer(self, offer: List[ButtonWidget]):
        STORAGE.set(f"offer", offer)

    @property
    def offer_copy(self):
        return STORAGE.get(f"offer_copy")

    @offer_copy.setter
    def offer_copy(self, offer: List[ButtonWidget]):
        STORAGE.set(f"offer_copy", offer)

    @property
    def display_offer(self):
        pages = split(self._size_offer_page, self.offer_copy)
        return pages[self.offer_page]
