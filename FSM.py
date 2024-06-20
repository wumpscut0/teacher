from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    input_text_to_admin = State()
    input_text_suggest_word = State()
    input_text_how_many_words = State()
    input_text_word_translate = State()
