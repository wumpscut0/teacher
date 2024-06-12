from alt_aiogram import TextMessageConstructor, ButtonWidget, OfferStorage
from alt_aiogram.markups.keyboards import LeftBackRight
from tools import Emoji


class Offer(TextMessageConstructor):
    def __init__(self):
        super().__init__()

    async def init(self):
        self.add_buttons_as_column(*OfferStorage().display_offer)
        self.add_buttons_in_new_row(ButtonWidget(text="Update global english run", callback_data="update_english_run"))
        left_back_right = LeftBackRight(
            left_callback_data="flip_left_offer",
            right_callback_data="flip_right_offer",
            back_text=f"Dismiss {Emoji.DENIAL}"
        )
        self.add_buttons_in_new_row(left_back_right.left, left_back_right.right)
        self.add_button_in_new_row(left_back_right.back)
