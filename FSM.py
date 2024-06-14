from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    input_text_to_admin = State()
    input_text_new_eng_word = State()
    input_text_new_rus_word = State()
    input_text_how_many_words = State()
    input_text_word_translate = State()
