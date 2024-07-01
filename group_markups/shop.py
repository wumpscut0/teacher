import os

from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile

from core.markups import ButtonWidget, TextWidget, WindowBuilder
from tools import Emoji


class SelectTypeContentCallbackData(CallbackData, prefix="select_type_content"):
    type: str


class SelectTypeContent(WindowBuilder):

    def __init__(self):
        super().__init__()
        self.add_texts_rows(TextWidget(text="Select content type"))
        for type_ in self.types:
            self.add_buttons_in_new_row(ButtonWidget(text=f"{type_}"))
