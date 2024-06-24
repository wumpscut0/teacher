import os
import string
from random import choice

import Levenshtein
from collections import defaultdict
from typing import List, Dict

from aiogram.types import FSInputFile

from FSM import States
from api import WordCard, WordCardSide
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
        super().__init__(type_="photo", backable=False)
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
        self.add_texts_rows(
            TextWidget(text="Suggest a ENGLISH word to Tuurngait that goes in the English Run.")
        )

    def suggest_another_word_display(self, suggest: str):
        self.add_texts_rows(
            TextWidget(text=f'"{suggest}" sent.\n\nSuggest another word')
        )


class English(WindowBuilder):
    _cleaner = str.maketrans("", "", string.punctuation.replace("-", "") + "№")

    def __init__(self, deck: List[WordCard], knowledge: Dict):
        super().__init__(
            state=States.input_text_word_translate,
        )
        self._deck = deck
        self.knowledge = knowledge
        self.current_card: WordCard | None = None
        self.current_side: WordCardSide | None = None
        self.current_question_widget: DataTextWidget | None = None
        self.deck_size = len(deck)
        self._rewards = defaultdict(int)
        self.dna = 0
        self.possible_dna = 0
        self.score = 0
        self.possible_score = 0
        self.back.text = f"Flush Run {Emoji.WAVE}"
        self.back.callback_data = "result_english_run"

        self._calculators = {
            "default:en-ru": self._calc_default_en_ru,
            "default:ru-en": self._calc_default_ru_en,
            "example:ru-en": self._calc_example,
            "example:en-ru": self._calc_example
        }

        self._grades_displaces = {
            "p": self._perfectly,
            "g": self._good,
            "b": self._bad
        }
        self.draw_card()
        translate_question_widget = DataTextWidget(text=f"\n{Emoji.ALCHEMY} Translate", data=self.current_side.question)
        self._questions_widgets = {
            "default:en-ru": DataTextWidget(
                text=f"\n{Emoji.ALCHEMY} Give all possible translations, comma-separated, of the word",
                data=self.current_side.question
            ),
            "default:ru-en": DataTextWidget(
                text=f"\n{Emoji.ALCHEMY} What English word can describe each of these words?",
                data='\n'.join(self.current_side.question), sep="\n"
            ),
            "example:ru-en": translate_question_widget,
            "example:en-ru": translate_question_widget
        }
        self.ask_question()

    def process_answer(self, answer: str):
        self.state = None
        grade, progress = self._calculators[self.current_side.type](answer)

        self.knowledge[self.current_card.word][self.current_side.type][grade] += 1

        self._info_display()
        self._open_card()
        self._progress_display()

        self.add_texts_rows(
            self.current_question_widget,
            DataTextWidget(text=f"\n{Emoji.VIOLET_ATOM} Your answer", data=answer),
        )

        if self.current_side.type == "default:en-ru":
            self.add_texts_rows(
                DataTextWidget(text=f"{Emoji.SPIRAL} Right answer", data="\n".join(self.current_side.answer) + "\n")
            )
        else:
            self.add_texts_rows(
                DataTextWidget(text=f"{Emoji.SPIRAL} Right answer", data=self.current_side.answer + "\n")
            )

        self._grades_displaces[grade](progress)

        # for threshold in range(5, self._possible_scores, 5):
        #     if threshold == self.score and not self._rewards[threshold] and os.path.exists(
        #             os.path.join(os.path.dirname(__file__), f"../images/{threshold}.jpg")):
        #         self._rewards[threshold] = 1
        #         self.photo = FSInputFile(os.path.join(os.path.dirname(__file__), f"../images/{threshold}.jpg"))
        #         self.type = "photo"
        #         break
        # else:
        #     self.type = "text"

    def _progress_display(self):
        p = 0
        g = 0
        for type_grade, level in self.knowledge[self.current_card.word][self.current_side.type].items():
            if type_grade.endswith("p") and level:
                p += 1
            elif type_grade.endswith("g") and level:
                g += 1

        knowledge = create_progress_text(
            numerator=int(0.5 * g + p),
            denominator=len(self._calculators),
            progress_element=Emoji.SQUARE_ACADEMIC_CAP,
            remaining_element=Emoji.BIOHAZARD
        )
        self.add_texts_rows(DataTextWidget(text=f"{Emoji.SQUARE_ACADEMIC_CAP} Knowledge level", data=knowledge))

    def _info_display(self):
        self.add_texts_rows(DataTextWidget(text=f"{Emoji.BOOKS_STACK} Stage", data=str(self.possible_score + 1)))
        self.add_texts_rows(DataTextWidget(text=f"{Emoji.DNA}", data=str(self.dna) + "\n", sep=""))

    def _calc_default_en_ru(self, answer: str):
        correct_answers = list(map(lambda x: x.strip().lower(), self.current_side.answer))
        user_answers = set(map(lambda x: x.strip().lower().strip().translate(self._cleaner), answer.split(",")))

        user_correct_answers = [user_answer for user_answer in user_answers if user_answer in correct_answers]

        progress = create_progress_text(
            numerator=len(user_correct_answers),
            denominator=len(correct_answers),
            length_widget=len(correct_answers),
            show_digits=False,
            progress_element=Emoji.DNA, remaining_element=Emoji.FLASK
        )
        self.possible_dna += len(progress)
        self.dna += progress.count(Emoji.DNA)
        self.possible_score += 1

        if len(user_correct_answers) >= len(correct_answers) // 2:
            return "p", progress
        elif len(user_correct_answers) > 0:
            return "g", progress
        else:
            return "b", progress

    def _calc_example(self, answer: str):
        correct_answer = " ".join(map(lambda x: x.strip(), self.current_side.answer.translate(self._cleaner).lower().split()))
        user_answer = " ".join(map(lambda x: x.strip(), answer.translate(self._cleaner).lower().split()))
        distance = Levenshtein.distance(user_answer, correct_answer)

        progress = create_progress_text(
            numerator=distance,
            denominator=len(correct_answer),
            length_widget=len(correct_answer.split()),
            show_digits=False,
            progress_element=Emoji.FLASK, remaining_element=Emoji.DNA
        )[::-1]

        if not distance:
            assert Emoji.FLASK not in progress
            return "p", progress
        elif progress.count(Emoji.DNA) >= len(progress) // 2:
            return "g", progress
        else:
            return "b", progress

    def _calc_default_ru_en(self, answer: str):
        correct_answer = self.current_side.answer.lower()
        user_answer = answer.lower().strip().translate(self._cleaner)
        distance = Levenshtein.distance(user_answer, correct_answer)
        progress = create_progress_text(
            numerator=distance,
            denominator=len(correct_answer),
            length_widget=len(correct_answer),
            show_digits=False,
            progress_element=Emoji.FLASK, remaining_element=Emoji.DNA
        )[::-1]
        if not distance:
            assert Emoji.FLASK not in progress
            return "p", progress
        elif distance < 3:
            return "g", progress
        else:
            return "b", progress

    def _calculate_dna(self, progress: str):
        self.possible_dna += len(progress)
        dna_count = progress.count(Emoji.DNA)
        self.dna += dna_count

    def _perfectly(self, progress: str):
        self._calculate_dna(progress)
        self.add_texts_rows(
            TextWidget(text=f"{Emoji.UNIVERSE} Perfectly! + {Emoji.DNA}x{len(progress)}")
        )
        self.score += 1

    def _good(self, progress):
        self._calculate_dna(progress)
        self.add_texts_rows(
            TextWidget(text=f"{Emoji.BRAIN} Good"),
            TextWidget(text=progress)
        )
        self.score += 1

    def _bad(self, progress: str):
        self._calculate_dna(progress)
        self.add_texts_rows(
            TextWidget(text=progress),
            TextWidget(text=f"{Emoji.BROKEN_ROSE} You can do better"),
        )

    def _open_card(self):
        data = self.current_card.data

        if data.get("audio"):
            self.voice = choice(data["audio"])
            self.type = "voice"
        else:
            self.type = "text"

        self.add_texts_rows(
            DataTextWidget(text=f"{Emoji.PUZZLE} Word", data=self.current_card.word),
            DataTextWidget(text=f"{Emoji.TALKING_HEAD} Transcription", data=data["ts"] + "\n")
        )

        self.add_buttons_in_new_row(
            ButtonWidget(text=f"{Emoji.OPEN_BOOK} Reference", callback_data="reference"),
            ButtonWidget(text=f"{Emoji.PLAY} Next", callback_data="draw_card")
        )

    def draw_card(self):
        self.type = "text"
        self.state = States.input_text_word_translate
        card = self._deck.pop()
        self.current_card = card
        self.current_side = card.get_random_side()

    def ask_question(self):
        self._info_display()
        question = self._questions_widgets[self.current_side.type]
        self.current_question_widget = question
        self.add_texts_rows(question)

    def reference(self):
        self.back.text = Emoji.BACK
        self.back.callback_data = "back"
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
        self.back.callback_data = "back"
        self.back.text = f"Ok"
