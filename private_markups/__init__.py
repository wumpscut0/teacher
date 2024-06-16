import os
from collections import defaultdict
from typing import List

from aiogram.types import FSInputFile

from FSM import States
from cache import Cache
from core import ButtonWidget, PhotoTextMessageConstructor, TextMessageConstructor, Emoji
from core.markups import DataTextWidget, TextWidget, Buttons


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


class Translate(TextMessageConstructor):
    def __init__(self, user_id: str | int, answer: str | None = None):
        super().__init__()
        self._cache = Cache(user_id)

        self._answer = answer

        if self._answer is not None:
            answer = self._answer.split(", ")
            for i_answer in answer:
                if i_answer not in self._cache.word[1].split(", "):
                    wrong_answer = DataTextWidget(text=f"{Emoji.DENIAL} Wrong answer", data=self._answer)
                    flip_card = DataTextWidget(text="Correct answer", data=f"{self._cache.word[1]}\n\n")
                    self.add_texts_rows(wrong_answer, flip_card)
                    break
            else:
                self.add_texts_rows(TextWidget(text=f"Correct {Emoji.OK}\n\n"))
                self._cache.score += 1

        self._new_word = self._cache.pop_word
        if self._new_word is not None:
            self.state = States.input_text_word_translate

        if self._new_word is None:
            continue_ = DataTextWidget(text=f"Your result", data=f"{self._cache.score}/{self._cache.possible_scores}")
            back = Buttons.back("Ok")
        else:
            continue_ = DataTextWidget(text=f"Translate", data=f"{self._new_word[0]}")
            back = Buttons.back(f"Cancel run{Emoji.DENIAL}")

        self.add_texts_rows(continue_)
        self.add_buttons_in_new_row(back)


class Reward(PhotoTextMessageConstructor):
    # TODO think about
    def __init__(self, photo: str | FSInputFile, text_map: List[TextWidget | DataTextWidget], keyboard_map: List[List[ButtonWidget]]):
        super().__init__(state=States.input_text_word_translate)
        self.photo = photo
        self.text_map = text_map
        self.keyboard_map = keyboard_map
