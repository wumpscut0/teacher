from collections import defaultdict
from typing import List

from core.redis import UserStorage, Storage
from database.models import WordModel


class Cache(UserStorage):
    @property
    def words(self):
        return self._get("words", [])

    @words.setter
    def words(self, words: List[List[str]]):
        self._set("words", words)

    @property
    def possible_scores(self):
        return self._get("possible_scores", 0)

    @possible_scores.setter
    def possible_scores(self, possible_scores: int):
        self._set("possible_scores", possible_scores)

    @property
    def word(self):
        return self._get("word", [])

    @word.setter
    def word(self, word: List[str]):
        self._set("word", word)

    @property
    def pop_word(self):
        words = self.words
        if words:
            word = words.pop()
            self.word = word
            self.words = words
            return word

    @property
    def score(self):
        return self._get("score", 0)

    @score.setter
    def score(self, score: int):
        self._set("score", score)

    @property
    def rewards(self):
        return self._get("rewards", defaultdict(int))

    @rewards.setter
    def rewards(self, rewards: defaultdict):
        self._set("rewards", rewards)

    ####################################################################################################################
    @property
    def new_eng_word(self):
        return self._get("new_eng_word")

    @new_eng_word.setter
    def new_eng_word(self, new_eng_word: str):
        self._set("new_eng_word", new_eng_word)

    def replenish_offer(self, translate: str):
        Offer().replenish_offer(WordModel(eng=self.new_eng_word, translate=translate.split(", ")))


class Offer(Storage):
    @property
    def offer(self):
        return self._get(f"offer", [])

    @offer.setter
    def offer(self, offer: List[WordModel]):
        self._set(f"offer", offer)

    def replenish_offer(self, word: WordModel):
        offer_list = self.offer
        offer_list.append(word)
        self.offer = offer_list
