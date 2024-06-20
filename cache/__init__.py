from tools import ImmuneList, ImmuneDict


class Offer(ImmuneList):
    def __init__(self):
        super().__init__("offer_list")

    @property
    def offer(self):
        return self._list


class TranslateCache(ImmuneDict):
    def __init__(self):
        super().__init__("translate_dict")


class WordDataCache(ImmuneDict):
    def __init__(self):
        super().__init__("word_data")
