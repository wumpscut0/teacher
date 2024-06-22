import os
import string
from random import randint, choice
from re import fullmatch, I

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


class SuggestWord(WindowBuilder):
    def __init__(self):
        super().__init__(
            unique=True,
            state=States.input_text_suggest_word,
            back_text=Emoji.BACK
        )
        self.prompt = "Suggest a ENGLISH word to Tuurngait that goes in the English Run."

    async def update(self, *args, **kwargs):
        self.add_texts_rows(
            TextWidget(text=self.prompt)
        )


class English(WindowBuilder):
    _cleaner = str.maketrans("", "", string.punctuation.replace("-", "") + "№")

    def __init__(self, deck: List[WordData]):
        super().__init__(state=States.input_text_word_translate)
        self._deck = deck
        self.current_card = None
        self.current_question = None
        self.current_answer = None
        self.card_is_default = None
        self.deck_size = len(deck)
        self._rewards = defaultdict(int)
        self.dna = 0
        self.possible_dna = 0
        self.score = 0
        self.back.text = f"Cancel run {Emoji.DENIAL}"
        self.question_widget = None

    @property
    def answer_as_text(self):
        if self.card_is_default and fullmatch(f"[а-я-, ]+", "".join(self.current_answer), flags=I):
            return ", ".join(self.current_answer)
        return self.current_answer

    async def update(self, answer: str):
        self.state = None
        self._open_card()
        self.add_texts_rows(
            self.question_widget,
            DataTextWidget(text=f"\n{Emoji.VIOLET_ATOM} Your answer", data=answer),
            DataTextWidget(text=f"{Emoji.SPIRAL} Right answer", data=self.answer_as_text + "\n")
        )

        progress, user_correct_answers = self._levenshtein_distance(answer)
        self.possible_dna += len(progress)
        dna_count = progress.count(Emoji.DNA)
        self.dna += dna_count
        if Emoji.FLASK not in progress:
            self.add_texts_rows(
                TextWidget(text=f"{Emoji.UNIVERSE} Perfectly! + {Emoji.DNA}x{len(progress)}")
            )
            self.score += 1
        elif not self.card_is_default:
            if dna_count >= len(progress) // 2:
                self.add_texts_rows(
                    TextWidget(text=f"{Emoji.BRAIN} Good"),
                    TextWidget(text=progress)
                )
                self.score += 1
            else:
                self.add_texts_rows(
                    TextWidget(text=progress),
                    TextWidget(text=f"{Emoji.BROKEN_ROSE} You can do better"),
                )
        else:
            if user_correct_answers:
                self.add_texts_rows(
                    TextWidget(text=f"{Emoji.BRAIN} Good"),
                    TextWidget(text=progress)
                )
                self.score += 1
            else:
                self.add_texts_rows(
                    TextWidget(text=progress),
                    TextWidget(text=f"{Emoji.BROKEN_ROSE} You can do better"),
                )

        # for threshold in range(5, self._possible_scores, 5):
        #     if threshold == self.score and not self._rewards[threshold] and os.path.exists(
        #             os.path.join(os.path.dirname(__file__), f"../images/{threshold}.jpg")):
        #         self._rewards[threshold] = 1
        #         self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), f"../images/{threshold}.jpg"))
        #         self.type = "photo"
        #         break
        # else:
        #     self.type = "text"

    def _levenshtein_distance(self, answer: str):
        if self.card_is_default:
            if isinstance(self.current_answer, list):
                correct_answers = list(map(lambda x: x.strip().lower(), self.current_answer))
                user_answers = set(map(lambda x: x.strip().lower().strip().translate(self._cleaner), answer.split(",")))
                distances = []
                user_correct_answers = []
                q_c = []
                for user_answer in user_answers:
                    comparison = []
                    for correct_answer in correct_answers:
                        comparison.append((Levenshtein.distance(user_answer, correct_answer), correct_answer))
                    d, q = min(comparison, key=lambda x: x[0])
                    q_c.append(q)
                    if not d:
                        user_correct_answers.append(user_answer)
                    distances.append(d)

                if len(user_answers) > len(correct_answers):
                    for _ in range(len(user_answers) - len(correct_answers)):
                        distances.remove(max(distances))

                progress = create_progress_text(
                    numerator=sum(distances),
                    denominator=len("".join(q_c)),
                    length_widget=len("".join(q_c)),
                    show_digits=False,
                    progress_element=Emoji.FLASK, remaining_element=Emoji.DNA
                )
                return progress[::-1], user_correct_answers
            else:
                correct_answers = [self.current_answer.lower()]
                user_answers = [answer.lower().strip().translate(self._cleaner)]
        else:
            correct_answers = [" ".join(map(lambda x: x.strip(), self.current_answer.translate(self._cleaner).lower().split()))]
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

        # if len(correct_answers) > 1:
        # progress = create_progress_text(
        #     numerator=round(sum(distances) / len(distances)),
        #     denominator=round(sum((len(answer) for answer in correct_answers)) / len(correct_answers)),
        #     length_widget=len(max(correct_answers, key=len)),
        #     show_digits=False,
        #     progress_element=Emoji.FLASK, remaining_element=Emoji.DNA
        # )
        progress = create_progress_text(
            numerator=sum(distances),
            denominator=len("".join(correct_answers)),
            length_widget=len("".join(correct_answers)),
            show_digits=False,
            progress_element=Emoji.FLASK, remaining_element=Emoji.DNA
        )
        return progress[::-1], user_correct_answers

    def _open_card(self):
        data = self.current_card.data

        if data["audio"]:
            self.voice = choice(data["audio"])
            self.type = "voice"
        else:
            self.type = "text"

        self.add_texts_rows(
            DataTextWidget(text=f"{Emoji.ALCHEMY} Word", data=self.current_card.word),
            DataTextWidget(text=f"{Emoji.TALKING_HEAD} Transcription", data=data["ts"])
        )

        self.add_buttons_in_new_row(
            ButtonWidget(text=f"{Emoji.OPEN_BOOK} Reference", callback_data="reference"),
            ButtonWidget(text=f"{Emoji.PLAY} Next", callback_data="draw_card")
        )

    def draw_card(self):
        self.type = "text"
        self.current_card = self._deck.pop()
        if randint(0, 1):
            card = self.current_card.get_random_default()
            self.card_is_default = True
        else:
            card = self.current_card.get_random_example()
            self.card_is_default = False
            if card is None:
                card = self.current_card.get_random_default()
                self.card_is_default = True
        self.current_question = card["original"]
        self.current_answer = card["translate"]
        self._ask_question()

    def _ask_question(self):
        self.state = States.input_text_word_translate
        if self.card_is_default and fullmatch(f"[а-я-, ]+", "".join(self.current_question), flags=I):
            q = DataTextWidget(text=f"\n{Emoji.ALCHEMY} What English word can describe each of these words?",
                           data='\n'.join(self.current_question), sep="\n")
            self.question_widget = q
            self.add_texts_rows(
                q
            )

        elif self.card_is_default:
            q = DataTextWidget(text=f"\n{Emoji.ALCHEMY} Give all possible translations, comma-separated, of the word", data=self.current_question)
            self.question_widget = q
            self.add_texts_rows(
                q
            )
        else:
            q = DataTextWidget(text=f"\n{Emoji.ALCHEMY} Translate", data=self.current_question)
            self.question_widget = q
            self.add_texts_rows(
                q
            )

    def reference(self):
        self.back.text = Emoji.BACK
        self.type = "text"
        self.state = None
        for pos, value in self.current_card.data["pos"].items():
            self.add_texts_rows(
                TextWidget(text=f"\n{Emoji.THOUGHT_BABBLE} as {pos}"),
                TextWidget(text=f"\n{Emoji.ABCD} Translates:"))
            for t in value.get("tr", []):
                self.add_texts_rows(TextWidget(text=t))
            self.add_texts_rows(TextWidget(text=f"\n{Emoji.CLIPS} Synonyms:"))
            for s in value.get("syn", []):
                self.add_texts_rows(TextWidget(text=s))
            examples = value.get("examples")
            if examples:
                self.add_texts_rows(TextWidget(text=f"\n{Emoji.LAMP} Examples:"))
                for example in value.get("examples", []):
                    self.add_texts_rows(
                        DataTextWidget(text=f"\n{example["original"]}", data=f"{example["translate"]}", sep="\n")
                    )

    def result(self):
        self.state = None
        self.type = "text"
        self.add_texts_rows(TextWidget(text="Your result\n"))
        self.add_texts_rows(
            DataTextWidget(text="Score", data=f"{self.score}/{self.deck_size}\n"),
            DataTextWidget(text=Emoji.DNA, data=f"{self.dna}/{self.possible_dna}")
        )
        self.back.text = f"Ok"
