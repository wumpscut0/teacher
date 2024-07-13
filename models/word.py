from copy import deepcopy
from typing import Dict

from aiogram.filters.callback_data import CallbackData

from api import SuperEnglishDictionary
from core import WindowBuilder
from core.markups import ButtonWidget
from tools import Emoji


class TranslateTickCallbackData(CallbackData, prefix="translate_tick"):
    index: int


class Word(WindowBuilder):
    def __init__(self, word: str, data: Dict):
        super().__init__(
            frozen_buttons_map=[
                [ButtonWidget(text=f"Save {Emoji.FLOPPY_DISC}", callback_data="merge_ru_default")]
            ]
        )
        self.word = word
        self.data = data
        buttons = []
        for i, tr in enumerate(SuperEnglishDictionary.get_translates(self.data)):
            buttons.append(ButtonWidget(text=tr, mark=Emoji.OK, callback_data=TranslateTickCallbackData(index=i)))
        self.paginated_buttons = buttons

    def tick_translate(self, index: int):
        if self.paginated_buttons[index].mark == Emoji.OK:
            self.paginated_buttons[index].mark = Emoji.DENIAL
        else:
            self.paginated_buttons[index].mark = Emoji.OK

    async def merge_ru_default(self):
        new_data = deepcopy(self.data)
        scaffold_list = [word_button.text for word_button in self.paginated_buttons if word_button.mark == Emoji.DENIAL]

        for pos, pos_content in self.data["pos"].items():
            trs = pos_content.get("tr", [])
            for tr in trs:
                if tr in scaffold_list:
                    new_data["pos"][pos]["tr"].remove(tr)

        await SuperEnglishDictionary.set_yandex_data(self.word, new_data)
