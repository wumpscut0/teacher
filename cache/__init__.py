from typing import List, Tuple

from aiogram.filters.callback_data import CallbackData

from core import ButtonWidget, Emoji
from core.redis import PrivateStorage, STORAGE
from core.tools import split


class Cache(PrivateStorage):
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


class OfferWordTickCallbackData(CallbackData, prefix="offer_word_tick"):
    index: int


class OfferStorage:
    _size_offer_page = 10

    @property
    def offer(self):
        offer_list = STORAGE.get(f"offer")
        if offer_list is None:
            return []
        return offer_list

    def replenish_offer(self, word: str):
        offer_list = self.offer
        offer_list.append(ButtonWidget(
            text=word,
            callback_data=OfferWordTickCallbackData(index=len(offer_list)),
            mark=Emoji.TICK)
        )
        self.offer = offer_list

    @property
    def offer_page(self):
        page = STORAGE.get(f"offer_page")
        if page is None:
            return 0
        return page

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
    def pages_offer(self):
        return split(self._size_offer_page, self.offer_copy)
