import os
from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile

from core import WindowBuilder, ButtonWidget, TextWidget

from core.tools import Emoji
from database.models import WordModel


class GroupPartyTitleScreen(WindowBuilder):
    def __init__(self):
        super().__init__(type_="photo", burying=False)
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/Tuurngaid.jpg"))

    async def init(self):
        self.keyboard_map = [
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


class WordTickCallbackData(CallbackData, prefix="word_tick"):
    index: int


class AcceptOffer(WindowBuilder):
    def __init__(self, data: List[WordModel]):
        super().__init__(data=[ButtonWidget(
            mark=Emoji.OK,
            text=f"{word.eng}:{", ".join(word.translate)}",
            callback_data=WordTickCallbackData(index=i)
        ) for i, word in enumerate(data)])

    async def init(self):
        self.add_texts_rows(TextWidget(text="I have some offer from the community"))
        self.add_buttons_as_column(
            *self.partitioned_data,
            ButtonWidget(
                text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
                callback_data="accept_offer"
            ),
            ButtonWidget(text=f"{Emoji.DENIAL} Dismiss", callback_data="drop_offer")
        )


class EditEnglishRun(WindowBuilder):
    def __init__(self, data: List[WordModel]):
        super().__init__(data=[ButtonWidget(
            mark=Emoji.OK,
            text=f"{word.eng}:{", ".join(word.translate)}",
            callback_data=WordTickCallbackData(index=i)
        ) for i, word in enumerate(data)])

    async def init(self):
        self.add_texts_rows(TextWidget(text=f"Edit English Run {Emoji.LIST_WITH_PENCIL}"))
        self.add_buttons_as_column(
            *self.partitioned_data,
            ButtonWidget(
                text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
                callback_data="accept_edit_english_run"
            ),
        )
