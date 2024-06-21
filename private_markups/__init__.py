import os
import string
from random import randint, choice

import Levenshtein
from collections import defaultdict
from typing import List

from aiogram.types import FSInputFile

from FSM import States
from api import WordData
from core import ButtonWidget, WindowBuilder
from core.markups import DataTextWidget, TextWidget
from tools import Emoji, create_progress_text


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


class English(WindowBuilder):
    _cleaner = str.maketrans("", "", string.punctuation.replace("-", "") + "№")

    def __init__(self, cards: List[WordData]):
        super().__init__(state=States.input_text_word_translate)
        self._cards = cards
        self._possible_scores = len(self._cards)
        self._pop_card()
        self._rewards = defaultdict(int)
        self._score = 0
        self.add_texts_rows(DataTextWidget(text=f"Translate", data=f"{self._current_card["original"]}"))
        self.back.text = f"Cancel run {Emoji.DENIAL}"

    async def update(self, answer: str):
        progress, user_correct_answers = self._levenshtein_distance(answer)
        if user_correct_answers:
            if Emoji.FLASK in progress:
                self.add_texts_rows(
                    DataTextWidget(text=f"{Emoji.BRAIN} Correct", data=answer),
                    DataTextWidget(text=progress)
                )
            else:
                self.add_texts_rows(
                    TextWidget(text=f"{Emoji.UNIVERSE} Perfectly!")
                )
            self._score += 1
        else:
            self.add_texts_rows(
                TextWidget(text=progress),
                DataTextWidget(text=f"{Emoji.BROKEN_ROSE} Wrong answer", data=answer),
            )
        self._open_card()
        try:
            self._pop_card()
        except IndexError:
            self.state = None
            self.add_texts_rows(DataTextWidget(text=f"Your result", data=f"{self._score}/{self._possible_scores}"))
            self.back.text = f"Ok"
        else:
            self.add_texts_rows(DataTextWidget(text=f"{Emoji.LAMP} Translate", data=f"{self._current_card["original"]}"))
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

    def _pop_card(self):
        if randint(0, 1):
            self._current_card = self._cards.pop().get_random_default()
            self._card_is_default = True
        else:
            self._current_card = self._cards.pop().get_random_example()
            self._card_is_default = False

    def _levenshtein_distance(self, answer: str):
        if self._card_is_default:
            if isinstance(self._current_card["translate"], list):
                correct_answers = list(map(lambda x: x.strip.lower(), self._current_card["translate"]))
                user_answers = set(map(lambda x: x.strip.lower().strip().translate(self._cleaner), answer.split(",")))
            else:
                correct_answers = [self._current_card["translate"].lower()]
                user_answers = [answer.lower().strip().translate(self._cleaner)]
        else:
            correct_answers = [" ".join(map(lambda x: x.strip(), self._current_card["translate"].translate(self._cleaner).lower().split()))]
            user_answers = [" ".join(map(lambda x: x.strip(), answer.translate(self._cleaner).lower().split()))]

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

    def _open_card(self):
        self.add_texts_rows(
            DataTextWidget(text="Word", data=self._current_card.word)
        )
        data = self._current_card.data
        if data["audio"]:
            self.voice = choice(data["audio"])
            self.type = "voice"
        else:
            self.type = "text"

        self.add_texts_rows(
            DataTextWidget(text="Transcription", data=data["ts"]),
        )
        for pos, value in data["pos"].items():
            self.add_texts_rows(
                TextWidget(text=f"\nas {pos}"),
                DataTextWidget(text="Translates", data=', '.join(value["tr"])),
                DataTextWidget(text="Synonyms", data=', '.join(value["syn"])),
            )
            for example in value.get("examples", []):
                self.add_texts_rows(
                    DataTextWidget(text="Examples", data=f"{example["original"]} -> {example["translate"]}")
                )
