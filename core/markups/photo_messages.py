from aiogram.types import FSInputFile

from core.markups import PhotoTextMessageConstructor, TextWidget, Buttons
from core.tools import Emoji


class Photo(PhotoTextMessageConstructor):
    def __init__(
            self,
            photo: str | FSInputFile,
            caption: str | None = None,
            back_text: str = f"Close {Emoji.DENIAL}"
    ):
        super().__init__()
        self.photo = photo
        if caption:
            self.add_texts_rows(TextWidget(text=caption))
        self.add_buttons_in_new_row(Buttons.back(back_text))
