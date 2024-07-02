import os
import string
from collections import defaultdict
from random import choice

import Levenshtein
from typing import List, Dict, Tuple

from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile

from FSM import States
from api import WordCard
from core import errors_alt_telegram
from core.markups import DataTextWidget, TextWidget, ButtonWidget, WindowBuilder
from tools import Emoji, create_progress_text


class BuyingContentCallbackData(CallbackData, prefix="buying_content_name"):
    name: str


class Shop(WindowBuilder):
    def __init__(self, shop: Dict):
        buttons = []
        for name, content in shop.items():
            button_text = name + "\n"
            for currency, cost in content["cost"].items():
                if int(cost) > 0:
                    button_text += f"{currency} {cost}"
            buttons.append(ButtonWidget(text=button_text, callback_data=BuyingContentCallbackData(name=name)))
        super().__init__(
            paginated_buttons=buttons,
            buttons_per_line=3,
            buttons_per_page=30,
        )

    def balance_display(self, dna: int = 0, cube: int = 0, star: int = 0):
        self.add_texts_rows(TextWidget(text=f"{Emoji.DNA} {dna} {Emoji.CUBE} {cube} {Emoji.STAR} {star}"))

