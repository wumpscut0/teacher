import os
from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile

from cache import Offer
from core import TextMessageConstructor, ButtonWidget, TextWidget, PhotoTextMessageConstructor

from core.markups import Buttons
from core.tools import Emoji, split
from database.models import WordModel


class GroupPartyTitleScreen(PhotoTextMessageConstructor):
    def __init__(self):
        super().__init__()

    async def init(self):
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/Tuurngaid.jpg"))
        keyboard_map = [
            [
                ButtonWidget(text=f"Get offer {Emoji.BOX}", callback_data="get_offer")
            ],
            [
                ButtonWidget(text=f"Edit English Run {Emoji.GLOBE_WITH_MERIDIANS}", callback_data="edit_english_run")
            ],
            [
                ButtonWidget(text="Tuurngaid, you can go", callback_data="exit")
            ]
        ]
        self.keyboard_map = keyboard_map


class WordTickCallbackData(CallbackData, prefix="word_tick"):
    index: int


class EditEnglishRun(TextMessageConstructor):
    _size_page = 10

    def __init__(self, english_run_data: List[WordModel] | None = None):
        super().__init__()
        self.page = 0
        self._english_run_data = english_run_data
        self.words = None
        back = Buttons.back()
        if english_run_data is None:
            self._topik = "I have some offer from the community"
            drop = ButtonWidget(text=f"{Emoji.DENIAL} Dismiss", callback_data="drop_offer")
            self._control = drop, back
            self._update_callback_data = "accept_offer"
        else:
            self._topik = f"Edit English Run {Emoji.LIST_WITH_PENCIL}"
            self._control = back,
            self._update_callback_data = "accept_edit_english_run"

    async def init(self):
        self.add_texts_rows(TextWidget(text=self._topik))
        if self._english_run_data is None:
            self.words = [ButtonWidget(
                mark=Emoji.OK,
                text=f"{word.eng}:{", ".join(word.translate)}",
                callback_data=WordTickCallbackData(index=i))
                for i, word in enumerate(split(self._size_page, Offer().offer, self.page))
            ]
        else:
            self.words = [ButtonWidget(
                mark=Emoji.OK,
                text=f"{word.eng}:{", ".join(word.translate)}",
                callback_data=WordTickCallbackData(index=i))
                for i, word in enumerate(split(self._size_page, self._english_run_data, self.page))
            ]
        self.add_buttons_as_column(*self.words)
        self.add_buttons_in_new_row(ButtonWidget(
            text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
            callback_data=self._update_callback_data
        ))
        if self._size_page < len(self.words):
            self.add_buttons_in_new_row(Buttons.left("flip_left_edit"), Buttons.right("flip_right_edit"))
        self.add_buttons_as_column(*self._control)
