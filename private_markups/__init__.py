import os

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State
from aiogram.types import FSInputFile

from FSM import States
from cache import Cache
from core import ButtonWidget, PhotoTextMessageConstructor, TextMessageConstructor, Emoji
from core.markups import DataTextWidget, TextWidget
from core.markups.photo_messages import Photo


class Greetings(PhotoTextMessageConstructor):
    def __init__(self):
        super().__init__()
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/Tuurngide.jpg"))
        self.add_texts_rows(TextWidget(text=f"Wellcome.\nI am Tuurngaid.\nI will pass on all my knowledge to you, step by step."))
        self.add_buttons_in_new_row(ButtonWidget(text="Ok", callback_data="reset_context"))


class PrivateTuurngaidTitleScreen(PhotoTextMessageConstructor):
    def __init__(self):
        super().__init__()
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/lV7-nxj4P_o.jpg"))

    async def init(self):
        keyboard_map = [
            [
                ButtonWidget(text="Run English", callback_data="run_english")
            ]
        ]
        self.keyboard_map = keyboard_map

# TODO rethink initializers


class Translate(TextMessageConstructor):
    def __init__(self, cache: Cache, *, answer: str | None = None, new_word: str | None = None):
        self._new_word = new_word
        if new_word is None:
            super().__init__()
        else:
            super().__init__(States.input_text_word_translate)
        self._answer = answer
        self._cache = cache

    async def init(self):
        if self._answer is not None:
            answer = self._answer.split(", ")
            word = self._cache.current_word
            for i_answer in answer:
                if i_answer not in word[1].split(", "):
                    flip_card = f"Wrong answer {Emoji.DENIAL}. Correct answer is {word[1]}\n\n"
                    break
            else:
                flip_card = f"Correct {Emoji.OK}\n\n"
                self._cache.score += 1
                if self._cache.score == 5:
                    await self._bot_control._create_photo_message(Photo, FSInputFile(
                        os.path.join(os.path.dirname(__file__), "../images/5.jpg")))
                elif self._cache.score == 10:
                    await self._bot_control._create_photo_message(Photo, FSInputFile(
                        os.path.join(os.path.dirname(__file__), "../images/10.jpg")))
        else:
            flip_card = ""

        if self._new_word is None:
            back_text = "Ok"
            text = f"{flip_card}Your result"
            data = f"{self._cache.score}/{self._cache.possible_scores}"
        else:
            back_text = f"Cancel {Emoji.DENIAL}"
            text = f"{flip_card}Translate"
            data = f"{self._new_word[0]}"

        self.add_texts_rows(DataTextWidget(text=text, data=data))
        self.add_button_in_new_row(ButtonWidget(text=back_text, callback_data="reset_context"))
