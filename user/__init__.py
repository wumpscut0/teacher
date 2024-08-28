from core.markups import ButtonWidget, WindowBuilder, TextWidget
from tools import Emoji


class Greetings(WindowBuilder):
    def __init__(self):
        super().__init__(type_="photo", back_text="Ok")
        self.photo = "AgACAgIAAx0Cf42o9wACA15mg-YkVdOLBKZkbHrWutoTHQwCDQACw98xG3rTIEjZ6iLaf38deAEAAwIAA3gAAzUE"
        self.add_texts_rows(TextWidget(
            text=f"Wellcome, human.\nI am Tuurngaid.\nI will pass on all my knowledge to you, step by step."
        ))


class PrivateTitleScreen(WindowBuilder):
    def __init__(self):
        super().__init__(
            type_="photo",
            auto_back=False,
            photo="AgACAgIAAx0Cf42o9wACA1lmg-KSXwhGC6Z6E3R00sYQ3cIKowACqt8xG3rTIEgLAn-plPmK1QEAAwIAA3MAAzUE",
            frozen_buttons_map=[
                [
                    ButtonWidget(text=f"Run English {Emoji.SQUARE_ACADEMIC_CAP}", callback_data="run_english")
                ],
                [
                    ButtonWidget(text=f"Inspect English Run {Emoji.OPEN_BOOK}", callback_data="inspect_english_run")
                ],
                [
                    ButtonWidget(text=f"Shop {Emoji.SHOP}", callback_data="shop")
                ],
                [
                    ButtonWidget(text=f"My collection {Emoji.PICTURE_2}", callback_data="collection")
                ]
            ]
        )

    async def __call__(self, bot_control):
        self.add_texts_rows(
            TextWidget(text=f"{Emoji.DNA} {await bot_control.user_storage.get_value_by_key("english:total_dna", 0)}"
                            f"  {Emoji.CUBE} {await bot_control.user_storage.get_value_by_key("english:keys", 0)}"),
        )
