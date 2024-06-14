import os

from aiogram.types import FSInputFile

from cache import EnglishRunStorage
from core import TextMessageConstructor, ButtonWidget, TextWidget, PhotoMessageConstructor
from core.markups.keyboards import LeftRight
from core.tools import Emoji


class GroupPartyTitleScreen(PhotoMessageConstructor):
    def __init__(self):
        super().__init__()

    async def init(self):
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/Tuurngide.jpg"))
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


class EditEnglishRun(TextMessageConstructor):
    def __init__(self):
        super().__init__()
        self._storage = EnglishRunStorage()
        back = ButtonWidget(text=Emoji.BACK, callback_data="return_to_context")
        if self._storage.current_edit_is_offer:
            self._topik = "I have some offer from the community"
            drop = ButtonWidget(text=f"{Emoji.DENIAL} Dismiss", callback_data="drop_offer")
            self._back_buttons = drop, back
            self._update_callback_data = "update_english_run"
        else:
            self._topik = f"Edit English Run {Emoji.LIST_WITH_PENCIL}"
            self._back_buttons = back,
            self._update_callback_data = "rewrite_english_run"

    async def init(self):
        self.add_texts_rows(TextWidget(text=self._topik))
        pages = self._storage.pages_edit
        self.add_buttons_as_column(*pages[self._storage.edit_page])
        self.add_buttons_in_new_row(ButtonWidget(
            text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
            callback_data=self._update_callback_data
        ))
        if len(pages) > 1:
            left_right = LeftRight(
                left_callback_data="flip_left_edit",
                right_callback_data="flip_right_edit",
            )
            self.merge(left_right)

        self.add_buttons_as_column(*self._back_buttons)
