from typing import List

from core.redis import Storage, ImmuneDict
from database.models import WordModel


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


class TranslateCache(ImmuneDict):
    def __init__(self):
        super().__init__("translate_dict")


class WordEntriesCache(ImmuneDict):
    def __init__(self):
        super().__init__("word_entries")


class YandexDictCache(ImmuneDict):
    def __init__(self):
        super().__init__("yandex_dict_cache")
