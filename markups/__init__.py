import os

from aiogram.types import FSInputFile

from cache import OfferStorage
from core import TextMessageConstructor, ButtonWidget, VoiceMessageConstructor, TextWidget
from core.markups.keyboards import LeftBackRight, LeftRight
from core.tools import Emoji


class PrivateTuurngaidTitleScreen(TextMessageConstructor):
    def __init__(self):
        super().__init__()

    async def init(self):
        keyboard_map = [
            [
                ButtonWidget(text="Run English", callback_data="run_english")
            ]
        ]
        self.keyboard_map = keyboard_map


class GroupPartyTitleScreen(VoiceMessageConstructor):
    def __init__(self):
        super().__init__()

    async def init(self):
        self.voice = FSInputFile(os.path.join(os.path.dirname(__file__), "../sounds/i_obey_you.ogg"))
        keyboard_map = [
            [
                ButtonWidget(text="Get offer", callback_data="get_offer")
            ],
            [
                ButtonWidget(text="Tuurngaid, you can go", callback_data="exit")
            ]
        ]
        self.keyboard_map = keyboard_map


class Offer(TextMessageConstructor):
    def __init__(self):
        super().__init__()

    async def init(self):
        self.add_texts_rows(TextWidget(text=f"I have some offer from community {Emoji.SIGHT}"))
        storage = OfferStorage()
        pages = storage.pages_offer
        self.add_buttons_as_column(*pages[storage.offer_page])
        self.add_buttons_in_new_row(ButtonWidget(text="Update global english run", callback_data="update_english_run"))
        if len(pages) > 1:
            left_right = LeftRight(
                left_callback_data="flip_left_offer",
                right_callback_data="flip_right_offer",
            )
            self.merge(left_right)
        back = ButtonWidget(text=f"{Emoji.DENIAL} Dismiss", callback_data="return_to_context")
        self.add_button_in_new_row(back)
