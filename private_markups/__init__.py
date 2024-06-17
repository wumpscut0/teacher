import os
from collections import defaultdict
from typing import List

from aiogram.types import FSInputFile
from pydantic import BaseModel

from FSM import States
from core import ButtonWidget, WindowBuilder, Emoji
from core.markups import DataTextWidget, TextWidget


class Greetings(WindowBuilder):
    def __init__(self):
        super().__init__(type_="photo", back_text="Ok")
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/Tuurngaid.jpg"))

    async def init(self):
        self.add_texts_rows(TextWidget(
            text=f"Wellcome, human.\nI am Tuurngaid.\nI will pass on all my knowledge to you, step by step."
        ))


class PrivateTuurngaidTitleScreen(WindowBuilder):
    def __init__(self):
        super().__init__(type_="photo", burying=False)
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/lV7-nxj4P_o.jpg"))

    async def init(self):
        self.keyboard_map = [
            [
                ButtonWidget(text="Run English", callback_data="run_english")
            ]
        ]


class Card(BaseModel):
    question: str
    answer: str


class English(WindowBuilder):
    def __init__(self, cards: List[Card]):
        super().__init__(state=States.input_text_word_translate, freeze=True)
        self.cards = cards
        self.current_card = self.cards.pop()
        self._rewards = defaultdict(int)
        self._possible_scores = len(self.cards)
        self.answer = None
        self._score = 0

    async def init(self):
        if self.answer is not None:
            for i_answer in self.answer.split(", "):
                if i_answer in self.current_card.answer.split(", "):
                    self.add_texts_rows(TextWidget(text=f"Correct {Emoji.OK}\n\n"))
                    self._score += 1
                    break
            else:
                self.add_texts_rows(
                    DataTextWidget(text=f"{Emoji.DENIAL} Wrong answer", data=self.answer),
                    DataTextWidget(text="Correct answer", data=f"{self.current_card.answer}\n\n")
                )
        try:
            self.current_card = self.cards.pop()
        except IndexError:
            self.state = None
            self.add_texts_rows(DataTextWidget(text=f"Your result", data=f"{self._score}/{self._possible_scores}"))
            self.back.text = f"Ok"
        else:
            self.add_texts_rows(DataTextWidget(text=f"Translate", data=f"{self.current_card.question}"))
            self.back.text = f"Cancel run {Emoji.DENIAL}"

        for threshold in range(5, self._possible_scores, 5):
            if threshold == self._score:
                if not self._rewards[threshold]:
                    self._rewards[threshold] = 1
                    self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), f"../images/{threshold}.jpg"))
                    self.type = "photo"
                break
        else:
            self.type = "text"
