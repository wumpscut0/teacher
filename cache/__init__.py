from typing import List

from aiogram.filters.callback_data import CallbackData

from core import ButtonWidget, Emoji
from core.redis import PrivateStorage, STORAGE
from core.tools import split


class Cache(PrivateStorage):
    @property
    def words(self):
        return STORAGE.get(f"words:{self._chat_id}")

    @words.setter
    def words(self, words: List[List[str]]):
        STORAGE.set(f"words:{self._chat_id}", words)

    @property
    def possible_scores(self):
        return STORAGE.get(f"possible_scores:{self._chat_id}")

    @possible_scores.setter
    def possible_scores(self, possible_scores: int):
        STORAGE.set(f"possible_scores:{self._chat_id}", possible_scores)

    @property
    def extract_word(self):
        words = self.words
        try:
            word = words.pop()
            self.words = words
            return word
        except IndexError:
            return

    @property
    def current_word(self):
        return STORAGE.get(f"current_word:{self._chat_id}")

    @current_word.setter
    def current_word(self, current_word: int):
        STORAGE.set(f"current_word:{self._chat_id}", current_word)

    @property
    def score(self):
        score = STORAGE.get(f"score:{self._chat_id}")
        if score is None:
            return 0
        return score

    @score.setter
    def score(self, score: int):
        STORAGE.set(f"score:{self._chat_id}", score)

    ####################################################################################################################
    @property
    def new_eng_word(self):
        return STORAGE.get(f"new_eng_word:{self._chat_id}")

    @new_eng_word.setter
    def new_eng_word(self, new_eng_word: str):
        STORAGE.set(f"new_eng_word:{self._chat_id}", new_eng_word)

    def replenish_offer(self, translate: str):
        EnglishRunStorage().replenish_offer(f"{self.new_eng_word}:{translate}")


class WordTickCallbackData(CallbackData, prefix="word_tick"):
    index: int


class EnglishRunStorage:
    _size_page = 10

    @property
    def current_edit_is_offer(self):
        return STORAGE.get(f"current_edit_is_offer")

    @current_edit_is_offer.setter
    def current_edit_is_offer(self, flag: bool):
        STORAGE.set(f"current_edit_is_offer", flag)

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
            callback_data=WordTickCallbackData(index=len(offer_list)),
            mark=Emoji.OK)
        )
        self.offer = offer_list
        print(self.offer)

    @offer.setter
    def offer(self, offer: List[ButtonWidget]):
        STORAGE.set(f"offer", offer)

    @property
    def edit_page(self):
        page = STORAGE.get(f"edit_page")
        if page is None:
            return 0
        return page

    @edit_page.setter
    def edit_page(self, page: int):
        STORAGE.set(f"edit_page", page)

    def flip_left_edit(self):
        STORAGE.set(f"edit_page", (self.edit_page - 1) % len(split(self._size_page, self.edit)))

    def flip_right_edit(self):
        STORAGE.set(f"edit_page", (self.edit_page + 1) % len(split(self._size_page, self.edit)))

    @property
    def edit(self):
        return STORAGE.get(f"edit")

    @edit.setter
    def edit(self, edit_buttons: List[ButtonWidget]):
        STORAGE.set(f"edit", edit_buttons)

    @property
    def pages_edit(self):
        return split(self._size_page, self.edit)
