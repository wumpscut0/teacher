import os.path
from typing import List, Literal, Any, Iterable, TypeVar

from aiogram.types import FSInputFile
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State

from tools import Emoji


class TextWidget:
    def __init__(
        self,
        *,
        mark: str = "",
        text: str = Emoji.BAN,
        mark_left: bool = True,
        sep: str = " ",
    ):
        self.mark = mark
        self._text = text
        self.mark_left = mark_left
        self.sep = sep

    @property
    def text(self):
        if self.mark_left:
            return Text(self.mark) + Text(self.sep) + Bold(self._text)
        return Bold(self._text) + Text(self.sep) + Text(self.mark)

    @text.setter
    def text(self, text: str):
        self._text = text


class DataTextWidget(TextWidget):
    def __init__(
        self,
        *,
        mark: str = "",
        text: str = Emoji.BAN,
        data: str = Emoji.GREY_QUESTION,
        sep: str = ": ",
        end: str = "",
    ):
        super().__init__(
            mark=mark,
            text=text,
        )
        self.data = data
        self.sep_ = sep
        self.end = end

    @property
    def text(self):
        return super().text + Text(self.sep_) + Italic(self.data) + Italic(self.end)


class ButtonWidget:
    def __init__(
        self,
        *,
        mark: str = "",
        text: str = None,
        mark_left: bool = True,
        sep: str = " ",
        callback_data: str | CallbackData = Emoji.BAN,
    ):
        self.mark = mark
        self._text = text
        self.mark_left = mark_left
        self.sep = sep
        self.callback_data = callback_data

    @property
    def only_text(self):
        return self.text.lstrip(self.mark + self.sep)

    @property
    def text(self):
        if self.mark_left:
            return self.mark + self.sep + self._text
        return self._text + self.sep + self.mark

    @text.setter
    def text(self, text: str):
        self._text = text


class TextMarkupConstructor:
    def __init__(self, map_: List[DataTextWidget | TextWidget] | None = None):
        super().__init__()
        self._text_map = [] if map_ is None else map_

    @property
    def text_map(self):
        return self._text_map

    @text_map.setter
    def text_map(self, map_: List[DataTextWidget | TextWidget]):
        self._text_map = map_

    def add_texts_rows(self, *args: DataTextWidget | TextWidget):
        for text in args:
            self._text_map.append(text)

    @property
    def text(self):
        try:
            return (as_list(*(text.text for text in self._text_map))).as_html()
        except IndexError:
            return ""


class KeyboardMarkupConstructor:
    """
    Max telegram inline keyboard buttons row is 8.
     add_button(s)_in_last_row will automatically move the button to the new row

     Max telegram inline keyboard buttons row is 4 with only emoji text in message.
     for this case toggle flag only_emoji_text=True

    """

    _limitation_row = 8
    _limitation_row_with_emoji = 4

    def __init__(self, map_: List[List[ButtonWidget]] | None = None):
        super().__init__()
        self._keyboard_map = [[]] if map_ is None else map_

    @property
    def keyboard_map(self):
        return self._keyboard_map

    @keyboard_map.setter
    def keyboard_map(self, map_: List[List[ButtonWidget]]):
        self._keyboard_map = map_

    def add_buttons_in_last_row(self, *buttons: ButtonWidget, only_emoji_text=False):
        if only_emoji_text:
            limitations_row = self._limitation_row_with_emoji
        else:
            limitations_row = self._limitation_row
        for button in buttons:
            if len(self._keyboard_map[-1]) == limitations_row:
                self.add_buttons_in_new_row(button)
            else:
                self._keyboard_map[-1].append(button)

    def add_buttons_in_new_row(self, *buttons: ButtonWidget, only_emoji_text=False):
        if only_emoji_text:
            limitations_row = self._limitation_row_with_emoji
        else:
            limitations_row = self._limitation_row
        self._keyboard_map.append([])
        limit = 0
        for button in buttons:
            if limit == limitations_row:
                limit = 0
                self.add_buttons_in_new_row(button)
            else:
                self.add_buttons_in_last_row(button, only_emoji_text=only_emoji_text)
            limit += 1

    def add_buttons_as_column(self, *buttons: ButtonWidget):
        for button in buttons:
            self.add_buttons_in_new_row(button)

    @property
    def keyboard(self):
        if self._keyboard_map == [[]]:
            return

        markup = InlineKeyboardBuilder()
        for buttons_row in self._keyboard_map:
            row = InlineKeyboardBuilder()
            for button in buttons_row:
                row.button(text=button.text, callback_data=button.callback_data)
            markup.attach(row)
        return markup.as_markup()


T = TypeVar("T")


class _MetaReturnUpdateSelf(type):
    @staticmethod
    def _self_returner(update):
        async def wrapper(self, *args, **kwargs):
            await update(self, *args, **kwargs)
            return self
        return wrapper

    def __new__(cls, name, bases, dct):
        instance = super().__new__(cls, name, bases, dct)
        instance.update = cls._self_returner(instance.update)
        return instance


class WindowBuilder(
    TextMarkupConstructor,
    KeyboardMarkupConstructor,
    metaclass=_MetaReturnUpdateSelf,
):
    _max_buttons = 100
    _max_symbols = 1024
    _available_types = "text", "photo", "audio"

    def __init__(
            self,
            *,
            unique: bool = True,
            type_: Literal["text", "photo", "audio"] = "text",
            state: str | State | None = None,
            photo: str | FSInputFile | None = None,
            voice: str | FSInputFile | None = None,
            text_map: list[DataTextWidget | TextWidget] | None = None,
            keyboard_map: list[list[ButtonWidget]] | None = None,
            burying: bool = True,
            back_text: str = Emoji.BACK,
            left_text: str = Emoji.LEFT,
            left_mark: str = "",
            right_text: str = Emoji.RIGHT,
            right_mark: str = "",
            size_page: int = 10,
            page: int = 0,
            data: list[Any] = None,
    ):
        TextMarkupConstructor.__init__(self, text_map)
        KeyboardMarkupConstructor.__init__(self, keyboard_map)
        if unique:
            self.id = str(id(self))
        else:
            self.id = "common"
        self.control_inited = False
        self._data = [] if data is None else data
        self._size_page = size_page
        if size_page > self._max_buttons:
            raise ValueError(f"Max size page is {self._max_buttons}")
        self._partitioned_data = self.split(size_page, self._data)
        self.burying = burying
        self.page = page
        self.type = type_
        self.state = state
        self._photo = photo
        self._voice = voice
        self.left = ButtonWidget(text=left_text, mark=left_mark, sep="", callback_data="flip_left")
        self.right = ButtonWidget(text=right_text, mark=right_mark, sep="", callback_data="flip_right")
        self.back = ButtonWidget(text=back_text, callback_data="bury")
        if len(self.text) > self._max_symbols:
            raise ValueError(f"Max symbols per message is {self._max_symbols}")
        if self.type not in self._available_types:
            raise ValueError(f"Available type is {self._available_types} not {self.type}")

    @property
    def data(self) -> List[Any]:
        return [item for page in self._partitioned_data for item in page]

    @data.setter
    def data(self, data: List[Any]):
        self._data = data

    @property
    def partitioned_data(self) -> List[Any]:
        return self._partitioned_data[self.page % len(self._partitioned_data)]

    @partitioned_data.setter
    def partitioned_data(self, partitioned_data: List[Any]):
        self._partitioned_data[self.page % len(self._partitioned_data)] = partitioned_data

    def init_control(self):
        if len(self._partitioned_data) > 1:
            self.add_buttons_in_new_row(self.left, self.right)
        if self.burying:
            self.add_buttons_in_new_row(self.back)
        self.control_inited = True

    def reset(self):
        self.text_map = []
        self.keyboard_map = [[]]
        self.control_inited = False

    @property
    def voice(self):
        if self._voice is None:
            return FSInputFile(os.path.join(os.path.dirname(__file__), "no_audio.ogg"))
        return self._voice

    @voice.setter
    def voice(self, voice: str | FSInputFile):
        self._voice = voice

    @property
    def photo(self):
        if not self._photo:
            return FSInputFile(os.path.join(os.path.dirname(__file__), "no_photo.jpg"))
        return self._photo

    @photo.setter
    def photo(self, photo: str | FSInputFile):
        self._photo = photo

    @staticmethod
    def split(size: int, items: Iterable[T]):
        lines = []
        line = []
        for item in items:
            if len(line) == size:
                lines.append(line)
                line = []
            line.append(item)
        lines.append(line)
        return lines

    async def update(self, *args, **kwargs):
        ...


class Info(WindowBuilder):
    def __init__(
        self,
        text: str,
        back_text: str = "Ok",
    ):
        super().__init__(unique=False, back_text=back_text)
        self.info = text

    async def update(self):
        self.add_texts_rows(TextWidget(text=self.info))


class Temp(WindowBuilder):
    def __init__(
        self,
        text: str = f"{Emoji.HOURGLASS_START} Processing...",
    ):
        super().__init__(unique=False, burying=False)
        self.info = text

    async def update(self):
        self.add_texts_rows(TextWidget(text=self.info))


class Input(WindowBuilder):
    def __init__(
        self,
        prompt: str,
        state: State | str,
        back_text: str = f"{Emoji.DENIAL} Cancel",
    ):
        super().__init__(unique=False, state=state, back_text=back_text)
        self.prompt = prompt

    async def update(self):
        self.add_texts_rows(TextWidget(text=self.prompt))


class Conform(WindowBuilder):
    def __init__(
        self,
        text: str,
        yes_callback_data: str | CallbackData,
        *,
        no_callback_data: str | CallbackData = "bury",
        yes_text: str = f"{Emoji.OK} Yes",
        no_text: str = f"{Emoji.DENIAL} No",
    ):
        super().__init__(unique=False, back_text=no_text, burying=False)
        self.yes_callback_data = yes_callback_data
        self.no_callback_data = no_callback_data
        self.yes_text = yes_text
        self.prompt = text
        self.no_text = no_text

    async def update(self):
        self.add_texts_rows(TextWidget(text=self.prompt))
        self.add_buttons_in_new_row(
            ButtonWidget(text=self.yes_text, callback_data=self.yes_callback_data),
            ButtonWidget(text=self.no_text, callback_data=self.no_callback_data)
        )
