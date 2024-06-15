import os

from aiogram.types import FSInputFile

from core.markups import VoiceTextMessageConstructor, ButtonWidget, Buttons


class Voice(VoiceTextMessageConstructor):
    def __init__(self, voice: str | FSInputFile, back_text="Ok"):
        super().__init__()
        self.voice = voice
        self.add_button_in_new_row(Buttons.back(back_text))
