import os

from aiogram.types import FSInputFile

from core.markups import VoiceTextMessageConstructor, Buttons


class Voice(VoiceTextMessageConstructor):
    def __init__(self, voice: str | FSInputFile, back_text="Ok"):
        super().__init__()
        self.voice = voice
        self.add_buttons_in_new_row(Buttons.back(back_text))
