import os
import string
from collections import defaultdict
from random import choice

import Levenshtein
from typing import List, Dict, Tuple

from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile

from FSM import States
from api import WordCard
from core import errors_alt_telegram
from core.markups import DataTextWidget, TextWidget, ButtonWidget, WindowBuilder
from tools import Emoji, create_progress_text


class Shop(WindowBuilder):
    def __init__(self):
        super().__init__()
