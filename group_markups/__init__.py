import os

from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile

from core.markups import ButtonWidget, TextWidget, WindowBuilder
from tools import Emoji


class GroupPartyTitleScreen(WindowBuilder):
    def __init__(self):
        super().__init__(type_="photo", backable=False)
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/Tuurngaid.jpg"))
        self.keyboard_map = [
            [
                ButtonWidget(text=f"Get offer {Emoji.BOX}", callback_data="get_offer")
            ],
            [
                ButtonWidget(text=f"Edit English Run {Emoji.GLOBE_WITH_MERIDIANS}", callback_data="edit_english_run")
            ],
            [
                ButtonWidget(text=f"Add content {Emoji.COLORS}", callback_data="add_content")
            ]
        ]


class WordTickCallbackData(CallbackData, prefix="word_tick"):
    index: int


class AcceptOffer(WindowBuilder):
    def __init__(self, data: set[str]):
        super().__init__(
            frozen=True,
            data=[ButtonWidget(
                mark=Emoji.OK,
                text=word,
                callback_data=WordTickCallbackData(index=i)
            ) for i, word in enumerate(data)])
        self.add_texts_rows(TextWidget(text="I have some offer from the community"))
        self.add_buttons_as_column(
            ButtonWidget(
                text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
                callback_data="accept_offer"
            ),
            ButtonWidget(text=f"{Emoji.DENIAL} Dismiss", callback_data="drop_offer")
        )


class EditEnglishRun(WindowBuilder):
    def __init__(self, data: set[str]):
        super().__init__(
            frozen=True,
            data=[ButtonWidget(
                mark=Emoji.OK,
                text=word,
                callback_data=WordTickCallbackData(index=i)
            ) for i, word in enumerate(data)])
        self.add_texts_rows(TextWidget(text=f"Edit English Run {Emoji.LIST_WITH_PENCIL}"))
        self.add_buttons_as_column(
            ButtonWidget(
                text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
                callback_data="accept_edit_english_run"
            ),
        )
