from core.markups import ButtonWidget, WindowBuilder
from tools import Emoji


class GroupTitleScreen(WindowBuilder):
    def __init__(self):
        super().__init__(
            type_="photo",
            auto_back=False,
            photo="AgACAgIAAx0Cf42o9wACA15mg-YkVdOLBKZkbHrWutoTHQwCDQACw98xG3rTIEjZ6iLaf38deAEAAwIAA3gAAzUE",
            frozen_buttons_map=[
                [
                    ButtonWidget(text=f"Get words offer {Emoji.BOX}", callback_data="add_words")
                ],
                [
                    ButtonWidget(text=f"Edit English Run {Emoji.PENCIL_2}", callback_data="edit_words")
                ],
                [
                    ButtonWidget(text=f"Add content {Emoji.COLORS}", callback_data="add_content")
                ],
                [
                    ButtonWidget(text=f"Edit shop {Emoji.PENCIL_2}", callback_data="edit_shop")
                ]
            ]
        )