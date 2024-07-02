from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    input_text_to_admin = State()
    input_text_suggest_word = State()
    input_text_word_translate = State()
    input_photo_audio_add_content = State()
    input_text_content_name = State()
    input_integer_dna_cost = State()
    input_integer_cube_cost = State()
    input_integer_star_cost = State()

