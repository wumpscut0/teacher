from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State

from FSM import States
from core.markups import ButtonWidget, TextWidget, WindowBuilder
from tools import Emoji


class GroupPartyTitleScreen(WindowBuilder):
    def __init__(self):
        super().__init__(
            type_="photo", auto_back=False,
            photo="AgACAgIAAx0Cf42o9wACA15mg-YkVdOLBKZkbHrWutoTHQwCDQACw98xG3rTIEjZ6iLaf38deAEAAwIAA3gAAzUE",
            frozen_buttons_map=[
                [
                    ButtonWidget(text=f"Get offer {Emoji.BOX}", callback_data="get_offer")
                ],
                [
                    ButtonWidget(text=f"Edit English Run {Emoji.GLOBE_WITH_MERIDIANS}",
                                 callback_data="edit_english_run")
                ],
                [
                    ButtonWidget(text=f"Add content {Emoji.COLORS}", callback_data="init_add_content")
                ]
            ]
        )


class WordTickCallbackData(CallbackData, prefix="word_tick"):
    index: int


class AcceptOffer(WindowBuilder):
    def __init__(self, words: set[str]):
        super().__init__(
            paginated_buttons=[ButtonWidget(
                mark=Emoji.OK,
                text=word,
                callback_data=WordTickCallbackData(index=i)
            ) for i, word in enumerate(words)],
            frozen_text_map=[
                TextWidget(text="I have some offer from the community")
            ],
            frozen_buttons_map=[
                [
                    ButtonWidget(
                        text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
                        callback_data="accept_offer"
                    )
                ],
                [
                    ButtonWidget(text=f"{Emoji.DENIAL} Dismiss", callback_data="drop_offer")
                ]
            ]
        )


class EditEnglishRun(WindowBuilder):
    def __init__(self, words: set[str]):
        super().__init__(
            paginated_buttons=[ButtonWidget(
                mark=Emoji.OK,
                text=word,
                callback_data=WordTickCallbackData(index=i)
            ) for i, word in enumerate(words)],
            frozen_text_map=[
                TextWidget(text=f"Edit English Run {Emoji.LIST_WITH_PENCIL}")
            ],
            frozen_buttons_map=[
                [
                    ButtonWidget(
                        text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
                        callback_data="accept_edit_english_run"
                    )
                ]
            ]
        )
