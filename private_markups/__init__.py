import os
from fractions import Fraction

import Levenshtein
from collections import defaultdict
from typing import List

from aiogram.types import FSInputFile
from pydantic import BaseModel

from FSM import States
from core import ButtonWidget, WindowBuilder, Emoji
from core.markups import DataTextWidget, TextWidget
from core.tools import create_progress_text


class Greetings(WindowBuilder):
    def __init__(self):
        super().__init__(type_="photo", back_text="Ok")
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/Tuurngaid.jpg"))
        self.add_texts_rows(TextWidget(
            text=f"Wellcome, human.\nI am Tuurngaid.\nI will pass on all my knowledge to you, step by step."
        ))


class PrivateTuurngaidTitleScreen(WindowBuilder):
    def __init__(self):
        super().__init__(type_="photo", burying=False)
        self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), "../images/lV7-nxj4P_o.jpg"))
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
        super().__init__(state=States.input_text_word_translate)
        self._cards = cards
        self._possible_scores = len(self._cards)
        self._current_card = self._cards.pop()
        self._rewards = defaultdict(int)
        self._score = 0
        self.add_texts_rows(DataTextWidget(text=f"Translate", data=f"{self._current_card.question}"))
        self.back.text = f"Cancel run {Emoji.DENIAL}"

    async def update(self, answer: str):
        self.add_texts_rows(DataTextWidget(text=f"{Emoji.OPEN_BOOK} Word", data=self._current_card.question + "\n\n"))
        progress, user_correct_answers = self._levenshtein_distance(answer)
        if user_correct_answers:

            self.add_texts_rows(
                DataTextWidget(text=f"{Emoji.BRAIN} Correct", data=", ".join(user_correct_answers)),

            )
            if len(user_correct_answers) != len(self._current_card.answer.split(", ")):
                self.add_texts_rows(
                    DataTextWidget(text=f"{Emoji.WRITING_HAND} Full answer", data=f"{self._current_card.answer}\n\n")
                )
            else:
                self.add_texts_rows(
                    TextWidget(text=f"{Emoji.UNIVERSE} Perfectly!\n\n")
                )
            self._score += 1
        else:
            self.add_texts_rows(
                TextWidget(text=progress),
                DataTextWidget(text=f"{Emoji.BROKEN_ROSE} Wrong answer", data=answer),
                DataTextWidget(text=f"{Emoji.HYGEUM} Correct answer", data=f"{self._current_card.answer}\n\n")
            )

        try:
            self._current_card = self._cards.pop()
        except IndexError:
            self.state = None
            self.add_texts_rows(DataTextWidget(text=f"Your result", data=f"{self._score}/{self._possible_scores}"))
            self.back.text = f"Ok"
        else:
            self.add_texts_rows(DataTextWidget(text=f"{Emoji.LAMP} Translate", data=f"{self._current_card.question}"))
            self.back.text = f"Cancel run {Emoji.DENIAL}"

        for threshold in range(5, self._possible_scores, 5):
            if threshold == self._score and not self._rewards[threshold] and os.path.exists(
                    os.path.join(os.path.dirname(__file__), f"../images/{threshold}.jpg")):
                self._rewards[threshold] = 1
                self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), f"../images/{threshold}.jpg"))
                self.type = "photo"
                break
        else:
            self.type = "text"

    def _levenshtein_distance(self, answer: str):
        user_answers = set(answer.split(", "))
        correct_answers = self._current_card.answer.split(", ")
        distances = []
        user_correct_answers = []
        for user_answer in user_answers:
            comparison = []
            for correct_answer in correct_answers:
                comparison.append(Levenshtein.distance(user_answer, correct_answer))
            d = min(comparison)
            if not d:
                user_correct_answers.append(user_answer)
            distances.append(d)

        if len(user_answers) > len(correct_answers):
            for _ in range(len(user_answers) - len(correct_answers)):
                distances.remove(max(distances))

        progress = create_progress_text(
            numerator=round(sum(distances) / len(distances)),
            denominator=round(sum((len(answer) for answer in correct_answers)) / len(correct_answers)),
            length_widget=len(max(correct_answers, key=len)),
            show_digits=False,
            progress_element=Emoji.FLASK, remaining_element=Emoji.DNA
        )
        return progress[::-1], user_correct_answers
