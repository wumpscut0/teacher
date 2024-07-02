from aiogram.filters.callback_data import CallbackData

from FSM import States
from core.markups import ButtonWidget, TextWidget, WindowBuilder
from tools import Emoji


class SelectTypeContentCallbackData(CallbackData, prefix="select_type_content"):
    type: str


class InputContent(WindowBuilder):
    def __init__(self):
        super().__init__(
            state=States.input_photo_audio_add_content,
            back_text=f"{Emoji.DENIAL} Cancel"
        )
        self.temp_dna_cost = 0
        self.temp_cube_cost = 0
        self.temp_star_cost = 0
        self.temp_name = Emoji.RED_QUESTION
        self.add_texts_rows(TextWidget(text=f"Send one photo {Emoji.PHOTO} or audio {Emoji.AUDIO}"))

    def edit_display(self):
        self.state = None
        self.back.text = f"Save {Emoji.FLOPPY_DISC}"
        self.back.callback_data = "add_content"

        self.add_texts_rows(TextWidget(text=f"{Emoji.PENCIL} {self.temp_name}\n"
                                            f"{Emoji.DNA} {self.temp_dna_cost} "
                                            f"{Emoji.CUBE} {self.temp_cube_cost} "
                                            f"{Emoji.STAR} {self.temp_star_cost} "))
        self.add_buttons_in_new_row(
            ButtonWidget(text=Emoji.PENCIL, callback_data="edit_name"),
            ButtonWidget(text=Emoji.DNA, callback_data="edit_dna_cost"),
            ButtonWidget(text=Emoji.CUBE, callback_data="edit_cube_cost"),
            ButtonWidget(text=Emoji.STAR, callback_data="edit_star_cost"),
        )

    def input_name_display(self):
        self.state = States.input_text_content_name
        self.back_as_cancel()
        self.add_texts_rows(TextWidget(text=f"Enter a content name {Emoji.PENCIL}\nMax length is 20"))

    def input_dna_cost_display(self):
        self.state = States.input_integer_dna_cost
        self.back_as_cancel()
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.DNA} as integer"))

    def input_cube_cost_display(self):
        self.state = States.input_integer_cube_cost
        self.back_as_cancel()
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.CUBE} as integer"))

    def input_star_cost_display(self):
        self.state = States.input_integer_star_cost
        self.back_as_cancel()
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.STAR} as integer"))

