from typing import List

from aiogram.filters.callback_data import CallbackData

from core import ButtonWidget, Emoji
from core.redis import UserStorage, Storage
from core.tools import split


class Cache(UserStorage):
    @property
    def words(self):
        return self.__get("words", [])

    @words.setter
    def words(self, words: List[List[str]]):
        self.__set("words", words)

    @property
    def possible_scores(self):
        return self.__get("possible_scores", 0)

    @possible_scores.setter
    def possible_scores(self, possible_scores: int):
        self.__set("possible_scores", possible_scores)

    @property
    def pop_word(self):
        words = self.words
        if words:
            word = words.pop()
            self.words = words
            return word

    @property
    def score(self):
        return self.__get("score", 0)

    @score.setter
    def score(self, score: int):
        self.__set("score", score)

    ####################################################################################################################
    @property
    def new_eng_word(self):
        return self.__get("new_eng_word")

    @new_eng_word.setter
    def new_eng_word(self, new_eng_word: str):
        self.__set("new_eng_word", new_eng_word)

    def replenish_offer(self, translate: str):
        EnglishRunStorage().replenish_offer(f"{self.new_eng_word}:{translate}")


class WordTickCallbackData(CallbackData, prefix="word_tick"):
    index: int


class EnglishRunStorage(Storage):
    _size_page = 10

    @property
    def offer(self):
        return self.__get(f"offer", [])

    @offer.setter
    def offer(self, offer: List[ButtonWidget]):
        self.__set(f"offer", offer)

    def replenish_offer(self, word: str):
        offer_list = self.offer
        offer_list.append(ButtonWidget(
            text=word,
            callback_data=WordTickCallbackData(index=len(offer_list)),
            mark=Emoji.OK)
        )
        self.offer = offer_list

    @property
    def edit_page(self):
        return self.__get(f"edit_page", 0)

    def flip_left_edit(self):
        self.__set(f"edit_page", (self.edit_page - 1) % len(split(self._size_page, self.edit)))

    def flip_right_edit(self):
        self.__set(f"edit_page", (self.edit_page + 1) % len(split(self._size_page, self.edit)))

    @property
    def edit(self):
        return self.__get(f"edit")

    @edit.setter
    def edit(self, edit: List[ButtonWidget]):
        self.__set(f"edit", edit)

    @property
    def pages_edit(self):
        return split(self._size_page, self.edit)
