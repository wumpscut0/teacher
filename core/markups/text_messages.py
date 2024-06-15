from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State

from core.markups import TextMessageConstructor, TextWidget, ButtonWidget, Buttons
from core.tools import Emoji


class Info(TextMessageConstructor):
    def __init__(
        self,
        text: str,
        back_text: str = "Ok",
    ):
        super().__init__()
        self.add_texts_rows(TextWidget(text=text))
        self.add_button_in_last_row(Buttons.back(back_text))


class Temp(TextMessageConstructor):
    def __init__(
        self,
        text: str = f"{Emoji.HOURGLASS_START} Processing...",
    ):
        super().__init__()
        self.add_texts_rows(TextWidget(text=text))


class Input(TextMessageConstructor):
    def __init__(
        self,
        text: str,
        *,
        back_text: str = f"{Emoji.DENIAL} Cancel",
        state: State | None = None,
    ):
        super().__init__(state)
        self.add_texts_rows(TextWidget(text=text))
        self.add_button_in_new_row(Buttons.back(text=back_text))


class Conform(TextMessageConstructor):
    def __init__(
        self,
        text: str,
        yes_callback_data: str | CallbackData,
        *,
        yes_text: str = f"{Emoji.OK} Yes",
        no_text: str = f"{Emoji.DENIAL} No",
    ):
        super().__init__()
        self.add_texts_rows(TextWidget(text=text))
        self.add_buttons_in_new_row(
            ButtonWidget(text=yes_text, callback_data=yes_callback_data),
            Buttons.back(text=no_text)
        )
