from typing import List

from core.redis import Storage
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
