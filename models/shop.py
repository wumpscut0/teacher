from typing import Literal

from aiogram.filters.callback_data import CallbackData

from FSM import States
from core import WindowBuilder, BotControl
from core.markups import ButtonWidget, TextWidget
from tools import Emoji


class BuyingContentCallbackData(CallbackData, prefix="buying_content"):
    name: str


class EditContentCallbackData(CallbackData, prefix="edit_content"):
    name: str


class Shop(WindowBuilder):
    _actions = {
        "buy": BuyingContentCallbackData,
        "edit": EditContentCallbackData
    }
    _headers = {
        "buy": Emoji.RED_QUESTION,
        "edit": f"Edit shop {Emoji.TAG}"
    }

    def __init__(self, action_type: Literal["buy", "edit"]):
        self.temp_balance = None
        self.action_type = action_type
        super().__init__(
                frozen_text_map=[
                    TextWidget(text=self._headers[action_type])
                ],
            )

    async def __call__(self, bot_control: BotControl):
        shop_data = await bot_control.bot_storage.get_value_by_key("shop", {})
        buttons = []
        for name, content in shop_data.items():
            button_text = name + " "
            for currency, cost in content["cost"].items():
                if int(cost) > 0:
                    button_text += f"{currency} {cost} "
            buttons.append(ButtonWidget(
                text=button_text,
                callback_data=self._actions[self.action_type](name=name))
            )
        self.paginated_buttons = buttons

    def balance_display(self, dna: int = 0, cube: int = 0, star: int = 0):
        self.temp_balance = {
            Emoji.DNA: dna,
            Emoji.CUBE: cube,
            Emoji.STAR: star
        }
        self.add_texts_rows(TextWidget(text=f"{Emoji.DNA} {dna} {Emoji.CUBE} {cube} {Emoji.STAR} {star}"))


class Content(WindowBuilder):
    def __init__(
            self,
            action_type: Literal["add", "edit"],
            *,
            content_type: Literal["photo", "audio"] | None = None,
            content: str | None = None,
            temp_name: str = Emoji.RED_QUESTION,
            temp_dna_cost: int = 0,
            temp_cube_cost: int = 0,
            temp_star_cost: int = 0,
    ):
        super().__init__(
            state=States.input_photo_audio_content,
            back_text=f"{Emoji.DENIAL} Cancel"
        )
        if content_type is not None:
            self.type = content_type
        if content_type == "photo":
            self.photo = content
        else:
            self.voice = content
        self.action_type = action_type
        self.temp_name = temp_name
        self.old_name = temp_name
        self.temp_dna_cost = temp_dna_cost
        self.temp_cube_cost = temp_cube_cost
        self.temp_star_cost = temp_star_cost

    def __call__(self, bot_control: BotControl):
        self.state = None
        self.add_texts_rows(TextWidget(text=f"{Emoji.PENCIL} {self.temp_name}\n"
                                            f"{Emoji.DNA} {self.temp_dna_cost} "
                                            f"{Emoji.CUBE} {self.temp_cube_cost} "
                                            f"{Emoji.STAR} {self.temp_star_cost} "))
        self.add_buttons_as_new_row(ButtonWidget(text=Emoji.COLORS, callback_data="edit_content"))
        self.add_buttons_as_new_row(
            ButtonWidget(text=Emoji.PENCIL, callback_data="edit_name"),
            ButtonWidget(text=Emoji.DNA, callback_data="edit_dna_cost"),
            ButtonWidget(text=Emoji.CUBE, callback_data="edit_cube_cost"),
            ButtonWidget(text=Emoji.STAR, callback_data="edit_star_cost"),
        )
        if self.action_type == "edit":
            self.add_buttons_as_new_row(ButtonWidget(
                text=f"Delete {self.temp_name} {Emoji.DENIAL}",
                callback_data="delete_content"
            ))
        self.add_buttons_as_new_row(ButtonWidget(text=f"Save {Emoji.FLOPPY_DISC}", callback_data="merge_content"))

    def input_content_display(self):
        self.state = States.input_photo_audio_content
        self.add_texts_rows(TextWidget(text=f"Send a content {Emoji.GIFT}\nPhoto {Emoji.PHOTO} or audio {Emoji.AUDIO}"))

    def input_name_display(self):
        self.state = States.input_text_content_name
        self.add_texts_rows(TextWidget(text=f"Enter a content name {Emoji.PENCIL}\nMax length is 20"))

    def input_dna_cost_display(self):
        self.state = States.input_integer_dna_cost
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.DNA} as integer"))

    def input_cube_cost_display(self):
        self.state = States.input_integer_cube_cost
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.CUBE} as integer"))

    def input_star_cost_display(self):
        self.state = States.input_integer_star_cost
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.STAR} as integer"))
