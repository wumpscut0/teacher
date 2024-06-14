from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile

from core.markups import PhotoMessageConstructor, TextWidget, ButtonWidget
from core.tools import Emoji


class Photo(PhotoMessageConstructor):
    def __init__(
            self,
            photo: str | FSInputFile,
            caption: str | None = None,
            back_callback_data: str | CallbackData = "return_to_context"
    ):
        super().__init__()
        self.photo = photo
        self._caption = caption
        self._back = ButtonWidget(text=f"{Emoji.DENIAL} Закрыть", callback_data=back_callback_data)

    async def init(self):
        if self._caption:
            self.add_texts_rows(TextWidget(text=self._caption))
        self.add_button_in_new_row(self._back)
