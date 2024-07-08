from typing import Literal, List, Dict, Tuple
import string
from random import choice

import Levenshtein
from aiogram.filters.callback_data import CallbackData

from FSM import States
from api import WordCard, SuperEnglishDictionary
from core import errors_alt_telegram, BotControl
from core.markups import DataTextWidget, TextWidget, ButtonWidget, WindowBuilder, Info
from tools import Emoji, create_progress_text


class WordTickCallbackData(CallbackData, prefix="word_tick"):
    index: int


class EditEnglish(WindowBuilder):
    _prompt = {
        "add": f"Edit English Run {Emoji.LIST_WITH_PENCIL}",
        "edit": "I have some offer from the community"
    }

    def __init__(self, action_type: Literal["add", "edit"], words: set[str]):
        self.action_type = action_type
        super().__init__(
            paginated_buttons=[ButtonWidget(
                mark=Emoji.OK,
                text=word,
                callback_data=WordTickCallbackData(index=i)
            ) for i, word in enumerate(words)],
            frozen_text_map=[
                TextWidget(text=self._prompt[action_type])
            ],
            frozen_buttons_map=[
                [
                    ButtonWidget(
                        text=f"Update global english run {Emoji.GLOBE_WITH_MERIDIANS}",
                        callback_data="merge_words"
                    )
                ],
            ]
        )
        if action_type == "add":
            self._dismiss_frozen_display()

    def _dismiss_frozen_display(self):
        self.frozen_buttons.add_buttons_as_new_row(ButtonWidget(
            text=f"{Emoji.DENIAL} Dismiss", callback_data="drop_offer"
        ))


class SuggestWords(WindowBuilder):
    def __init__(self):
        super().__init__(
            state=States.input_text_suggest_word,
            back_text=Emoji.BACK
        )
        self.add_texts_rows(
            TextWidget(text="Suggest a ENGLISH words spaces-separated. They could to supply the English Run.")
        )

    def suggest_another_word_display(self, suggest: str):
        self.add_texts_rows(
            TextWidget(text=f'"{suggest}" sent.\n\nSuggest another word')
        )


def knowledge_as_progress_string(user_knowledge: Dict, knowledge_border: int, show_digits: bool = True):
    """
    :param show_digits:
    :param user_knowledge: extractable as dict as value by key, where key is word from dict english:knowledge from user_storage
    :param knowledge_border: equal possible stars, equal questions types by word. Extractable from knowledge_schema len
    :return:
    """
    p = 0
    g = 0
    for question_type, grades in user_knowledge.items():
        if grades.get("p"):
            p += 1
        elif grades.get("g"):
            g += 1

    return create_progress_text(
        show_digits=show_digits,
        numerator=int(0.5 * g + p),
        denominator=knowledge_border,
        length_widget=knowledge_border,
        progress_element=Emoji.STAR,
        remaining_element=Emoji.DARK_START

    )


class English(WindowBuilder):
    _cleaner = str.maketrans("", "", string.punctuation.replace("-", "") + "№")

    def __init__(self, deck: List[WordCard]):
        super().__init__(
            state=States.input_text_word_translate,
            back_callback_data="request_to_flush_run",
            back_text=f"Flush Run {Emoji.WAVE}"
        )
        self._deck = deck
        self._deck_size = len(deck)
        self._temp_current_card: WordCard | None = None

        self._temp_knowledge: Dict | None = None

        self._temp_dna = 0
        self._temp_past_dna = 0
        self._temp_possible_dna = 0

        self._temp_cube = 0
        self._temp_past_cube = 0
        self._temp_possible_cube = 0

        self._temp_progress: str
        self._temp_grade: str

        self._count_right_answers = 0
        self._count_possible_right_answers = 0

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

    async def process_answer(self, answer: str, bot_control: BotControl):
        self.type = "text"
        self.state = None
        self._count_possible_right_answers += 1

        self._calculators[self._temp_current_card.type](answer)

        user_knowledge = await bot_control.user_storage.get_value_by_key("english:knowledge", {})
        word_knowledge = user_knowledge.get(self._temp_current_card.word, self._temp_current_card.knowledge_scheme)
        word_knowledge[self._temp_current_card.type][self._temp_grade] += 1
        user_knowledge[self._temp_current_card.word] = word_knowledge
        self._temp_knowledge = user_knowledge
        await bot_control.user_storage.set_value_by_key("english:knowledge", user_knowledge)

        new_dna = await bot_control.user_storage.get_value_by_key("english:total_dna", 0) + self._temp_dna
        await bot_control.user_storage.set_value_by_key("english:total_dna", new_dna)

        new_keys = await bot_control.user_storage.get_value_by_key("english:keys", 0) + self._temp_cube
        await bot_control.user_storage.set_value_by_key("english:keys", new_keys)

        self._stage_display()
        self._word_info_display()
        self._knowledge_display()
        self._question_display()
        self._comparison_answer_display(answer)
        self._grades_displaces[self._temp_grade]()
        self._temp_past_dna += self._temp_dna
        self._temp_past_cube += self._temp_cube

    def _comparison_answer_display(self, answer):
        if self._temp_current_card.type == "default:en-ru":
            r = DataTextWidget(text=f"\n{Emoji.SHINE_STAR} Right answer",
                               data="\n".join(self._temp_current_card.answer) + "\n", sep=":\n")
        else:
            r = DataTextWidget(text=f"\n{Emoji.SHINE_STAR} Right answer", data=self._temp_current_card.answer + "\n")
        self.add_texts_rows(
            r,
            DataTextWidget(text=f"\n{Emoji.LIST_WITH_PENCIL} Your answer", data=answer + "\n")
        )

    def _knowledge_display(self):
        progress = knowledge_as_progress_string(self._temp_knowledge[self._temp_current_card.word], self._temp_current_card.knowledge_border)
        self.add_texts_rows(DataTextWidget(text=f"{Emoji.SQUARE_ACADEMIC_CAP} Knowledge level", data=progress))

    def _stage_display(self):
        self.add_texts_rows(
            DataTextWidget(text=f"{Emoji.BOOKS_STACK} Stage", data=str(self._count_possible_right_answers)))

    def _calc_default_en_ru(self, answer: str):
        correct_answers = list(map(lambda x: x.strip().lower(), self._temp_current_card.answer))
        user_answers = set(map(lambda x: x.strip().lower().translate(self._cleaner), answer.split()))

        user_correct_answers = [user_answer for user_answer in user_answers if user_answer in correct_answers]

        self._temp_progress = create_progress_text(
            numerator=len(user_correct_answers) * 2,
            denominator=len(correct_answers) * 2,
            length_widget=len(correct_answers) * 2,
            show_digits=False,
            progress_element=Emoji.DNA, remaining_element=Emoji.FLASK
        )
        self._calculate_dna()

        if len(user_correct_answers) >= len(correct_answers) // 2:
            self._temp_grade = "p"
        elif len(user_correct_answers) > 0:
            self._temp_grade = "g"
        else:
            self._temp_grade = "b"

    def _calc_example(self, answer: str):
        correct_answer = " ".join(
            map(lambda x: x.strip(), self._temp_current_card.answer.translate(self._cleaner).lower().split()))
        user_answer = " ".join(map(lambda x: x.strip(), answer.translate(self._cleaner).lower().split()))
        distance = Levenshtein.distance(user_answer, correct_answer)

        self._temp_progress = create_progress_text(
            numerator=distance,
            denominator=len(correct_answer),
            length_widget=len(correct_answer.split()),
            show_digits=False,
            progress_element=Emoji.CHAINS, remaining_element=Emoji.CUBE
        )[::-1]
        self._calculate_cube()

        if not distance:
            assert Emoji.CHAINS not in self._temp_progress
            self._temp_grade = "p"
        elif self._temp_cube >= len(self._temp_progress) // 2:
            self._temp_grade = "g"
        else:
            self._temp_grade = "b"

    def _calc_default_ru_en(self, answer: str):
        correct_answer = self._temp_current_card.answer.lower()
        user_answer = answer.lower().strip().translate(self._cleaner)
        distance = Levenshtein.distance(user_answer, correct_answer)
        self._temp_progress = create_progress_text(
            numerator=distance,
            denominator=len(correct_answer),
            length_widget=len(correct_answer),
            show_digits=False,
            progress_element=Emoji.FLASK, remaining_element=Emoji.DNA
        )[::-1]
        self._calculate_dna()

        if not distance:
            assert Emoji.FLASK not in self._temp_progress
            self._temp_grade = "p"
        elif distance < 3:
            self._temp_grade = "g"
        else:
            self._temp_grade = "b"

    def _calculate_dna(self):
        self._temp_possible_dna += len(self._temp_progress)
        self._temp_dna += self._temp_progress.count(Emoji.DNA)

    def _calculate_cube(self):
        self._temp_possible_cube += len(self._temp_progress)
        self._temp_cube += self._temp_progress.count(Emoji.CUBE)

    def _perfectly(self):
        if self._temp_current_card.type.startswith("default"):
            self.add_texts_rows(
                TextWidget(
                    text=f"\n{self._temp_progress} {Emoji.ALCHEMY} {Emoji.DNA} {self._temp_past_dna} + {self._temp_dna}\n{Emoji.UNIVERSE} Perfectly!"
                )
            )
        else:
            self.add_texts_rows(
                TextWidget(
                    text=f"\n{self._temp_progress} {self._temp_past_cube} + {self._temp_cube}\n{Emoji.UNIVERSE} Perfectly!"
                )
            )
        self._count_right_answers += 1

    def _good(self):
        if self._temp_current_card.type.startswith("default"):
            self.add_texts_rows(
                TextWidget(
                    text=f"\n{self._temp_progress} {Emoji.ALCHEMY} {Emoji.DNA} {self._temp_past_dna} + {self._temp_progress.count(Emoji.DNA)}\n{Emoji.BRAIN} Good!"
                )
            )
        else:
            self.add_texts_rows(
                TextWidget(
                    text=f"\n{self._temp_progress} {self._temp_past_cube} + {self._temp_cube}\n{Emoji.BRAIN} Good!"
                )
            )
        self._count_right_answers += 1

    def _bad(self):
        if self._temp_current_card.type.startswith("default"):
            if Emoji.DNA not in self._temp_progress:
                self.add_texts_rows(
                    TextWidget(
                        text=f"\n{self._temp_progress} {Emoji.ALCHEMY} {Emoji.DNA} {self._temp_past_dna} + {self._temp_progress.count(Emoji.DNA)}\n{Emoji.BIOHAZARD}"
                    )
                )
            else:
                self.add_texts_rows(
                    TextWidget(
                        text=f"\n{self._temp_progress} {Emoji.ALCHEMY} {Emoji.DNA} {self._temp_past_dna} + {self._temp_progress.count(Emoji.DNA)}\n{Emoji.BROKEN_ROSE} You can do better!"
                    )
                )
        else:
            if Emoji.CUBE not in self._temp_progress:
                self.add_texts_rows(
                    TextWidget(
                        text=f"\n{self._temp_progress} {self._temp_past_cube} + {self._temp_progress.count(Emoji.CUBE)}\n{Emoji.BIOHAZARD}"
                    )
                )
            else:
                self.add_texts_rows(
                    TextWidget(
                        text=f"\n{self._temp_progress} {self._temp_past_cube} + {self._temp_progress.count(Emoji.CUBE)}\n{Emoji.BROKEN_ROSE} You can do better!"
                    )
                )

    def _word_info_display(self):
        data = self._temp_current_card.data

        if data.get("audio"):
            self.voice = choice(data["audio"])
            self.type = "voice"
        else:
            self.type = "text"

        self.add_texts_rows(DataTextWidget(text=f"{Emoji.PUZZLE} Word", data=self._temp_current_card.word))

        ts = data.get("ts")
        if ts:
            self.add_texts_rows(DataTextWidget(text=f"{Emoji.TALKING_HEAD} Transcription", data=ts + "\n"))

        self.add_buttons_as_new_row(
            ButtonWidget(text=f"{Emoji.OPEN_BOOK} Reference", callback_data="reference"),
            ButtonWidget(text=f"{Emoji.PLAY} Next", callback_data="draw_card")
        )

    def draw_card(self):
        self.type = "text"
        self.state = States.input_text_word_translate
        card = self._deck.pop()
        self._temp_current_card = card
        self._question_display()

    def _question_display(self):
        if self._temp_current_card.type == "default:ru-en":
            self.add_texts_rows(DataTextWidget(text=f"\n{Emoji.ALCHEMY} {self._temp_current_card.question_text}",
                                               data="\n".join(self._temp_current_card.question), sep="\n"))
        else:
            self.add_texts_rows(DataTextWidget(text=f"\n{Emoji.ALCHEMY} {self._temp_current_card.question_text}",
                                               data=self._temp_current_card.question))

    def reference(self):
        self.back.text = Emoji.BACK
        self.back.callback_data = "back"
        self.type = "text"
        self.state = None
        self.add_texts_rows(TextWidget(text=f"{Emoji.PUZZLE} {self._temp_current_card.word}"))
        for pos, pos_content in self._temp_current_card.data["pos"].items():
            self.add_texts_rows(
                TextWidget(
                    text=f"\n{Emoji.CHAIN_SEPARATOR * 3}\n\n{Emoji.THOUGHT_BABBLE} as {pos} {Emoji.THOUGHT_BABBLE}"),
            )
            trs = pos_content.get("tr", [])
            if trs:
                self.add_texts_rows(TextWidget(text=f"\n{Emoji.ABCD} Translates:"))
                for t in trs:
                    self.add_texts_rows(TextWidget(text=t))

            syns = pos_content.get("syn", [])
            if syns:
                self.add_texts_rows(TextWidget(text=f"\n{Emoji.CLIPS} Synonyms:"))
                for s in syns:
                    self.add_texts_rows(TextWidget(text=s))

            examples = pos_content.get("examples")
            if examples:
                self.add_texts_rows(TextWidget(text=f"\n{Emoji.LAMP} Examples:"))
                for example in examples:
                    try:
                        self.add_texts_rows(
                            DataTextWidget(text=f"\n{example["original"]}", data=f"{example["translate"]}", sep="\n")
                        )
                    except KeyError:
                        errors_alt_telegram.error(f"Impossible show up some example for word: {self._temp_current_card.word}",
                                                  exc_info=True)

    def result(self):
        self.state = None
        self.type = "text"
        self.add_texts_rows(TextWidget(text="Your result\n"))
        self.add_texts_rows(
            DataTextWidget(text="Right answers",
                           data=f"{self._count_right_answers}/{self._count_possible_right_answers}\n"),
            DataTextWidget(text=Emoji.DNA, data=f"{self._temp_dna}/{self._temp_possible_dna}", sep=""),
            DataTextWidget(text=Emoji.CUBE, data=f"{self._temp_cube}/{self._temp_possible_cube}", sep="")
        )
        self.back.callback_data = "back"
        self.back.text = f"Ok"


class BanWordCallbackData(CallbackData, prefix="ban_word"):
    word: str
    index: int


class InspectEnglishRun(WindowBuilder):
    def __init__(self):
        super().__init__(
            frozen_buttons_map=[
                [
                    ButtonWidget(text=f"Ban all {Emoji.DENIAL}", callback_data="ban_all"),
                    ButtonWidget(text=f"Unban all {Emoji.OK}", callback_data="unban_all")
                ],
            ],
        )

    async def __call__(self, bot_control: BotControl):
        words = await bot_control.bot_storage.get_value_by_key("words")
        words_ = []
        for word in words:
            data = await SuperEnglishDictionary.extract_data(word)
            if data["pos"]:
                knowledge_size = len(SuperEnglishDictionary.build_knowledge_schema(data))
                words_.append((word, knowledge_size))

        knowledge = await bot_control.user_storage.get_value_by_key("english:knowledge", {})
        ban_list = await bot_control.user_storage.get_value_by_key("english:ban_list", set())
        buttons = []
        stars = 0
        possible_star = 0
        for i, x in enumerate(words):
            word, knowledge_size = x
            progress = knowledge_as_progress_string(knowledge.get(word, {}), knowledge_size, show_digits=False)
            stars += progress.count(Emoji.STAR)
            possible_star += len(progress)
            buttons.append(ButtonWidget(
                text=f"{word} {progress}",
                mark=Emoji.OK if word not in ban_list else Emoji.DENIAL,
                callback_data=BanWordCallbackData(index=i, word=word)
            ))
        self.paginated_buttons = buttons
        self.frozen_text.add_texts_rows(TextWidget(text=f"{Emoji.STAR} {stars}/{possible_star}"))

    async def banning(self, bot_control: BotControl, index: int, word: str):
        ban_list = await bot_control.user_storage.get_value_by_key("english:ban_list", set())
        if self.paginated_buttons[index].mark == Emoji.OK:
            self.paginated_buttons[index].mark = Emoji.DENIAL
            ban_list.add(word)
        else:
            self.paginated_buttons[index].mark = Emoji.OK
            ban_list.remove(word)
        await bot_control.user_storage.set_value_by_key("english:ban_list", ban_list)

    async def ban_all(self, bot_control: BotControl):
        words = await bot_control.bot_storage.get_value_by_key("words")
        await bot_control.user_storage.set_value_by_key("english:ban_list", set(words))
        for button in self.paginated_buttons:
            button.mark = Emoji.DENIAL

    async def unban_all(self, bot_control: BotControl):
        await bot_control.user_storage.destroy_key("english:ban_list")
        for button in self.paginated_buttons:
            button.mark = Emoji.OK
