import os

from aiogram.types import FSInputFile

from cache import EnglishRunStorage
from core import TextMessageConstructor, ButtonWidget, TextWidget, PhotoTextMessageConstructor

from core.markups import Buttons
from core.tools import Emoji


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


class EditEnglishRun(TextMessageConstructor):
    def __init__(self):
        super().__init__()
        self._storage = EnglishRunStorage()
        back = Buttons.back()
        if self._storage.current_edit_is_offer:
            self._topik = "I have some offer from the community"
            drop = ButtonWidget(text=f"{Emoji.DENIAL} Dismiss", callback_data="drop_offer")
            self._back_buttons = drop, back
            self._update_callback_data = "update_english_run"
        else:
            self._topik = f"Edit English Run {Emoji.LIST_WITH_PENCIL}"
            self._back_buttons = back,
            self._update_callback_data = "rewrite_english_run"

        self.add_texts_rows(TextWidget(text=self._topik))
        pages = self._storage.pages_edit
        self.add_buttons_as_column(*pages[self._storage.edit_page])
        self.add_buttons_in_new_row(ButtonWidget(
            text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
            callback_data=self._update_callback_data
        ))
        if len(pages) > 1:
            self.add_buttons_in_new_row(Buttons.left("flip_left_edit"), Buttons.right("flip_right_edit"))

        self.add_buttons_as_column(*self._back_buttons)
