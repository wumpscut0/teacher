import os.path
from typing import List, Literal, Any, Iterable, TypeVar

from aiogram.types import FSInputFile
from aiogram.utils.formatting import as_list, Text, Bold, Italic
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State

from tools import Emoji


T = TypeVar("T")


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
        self.text = text
        self.mark_left = mark_left
        self.sep = sep

    @property
    def formatted_text(self):
        if self.mark_left:
            return Text(self.mark) + Text(self.sep) + Bold(self.text)
        return Bold(self.text) + Text(self.sep) + Text(self.mark)


class DataTextWidget:
    def __init__(
        self,
        *,
        mark: str = "",
        mark_sep: str = " ",
        text: str = Emoji.BAN,
        data: str = Emoji.GREY_QUESTION,
        sep: str = ": ",
        end: str = "",
    ):
        self.mark = mark
        self.mark_sep = mark_sep
        self.text = text
        self.data = data
        self.sep = sep
        self.end = end

    @property
    def formatted_text(self):
        return Text(self.mark) + Text(self.mark_sep) + Bold(self.text) + Text(self.sep) + Italic(self.data) + Italic(self.end)


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
        self.text = text
        self.mark_left = mark_left
        self.sep = sep
        self.callback_data = callback_data

    @property
    def formatted_text(self):
        if self.mark_left:
            return self.mark + self.sep + self.text
        return self.text + self.sep + self.mark


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
    def as_html(self):
        try:
            return (as_list(*(text.formatted_text for text in self._text_map))).as_html()
        except IndexError:
            return "No Data"


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
                row.button(text=button.formatted_text, callback_data=button.callback_data)
            markup.attach(row)
        return markup.as_markup()


class WindowBuilder(
    TextMarkupConstructor,
    KeyboardMarkupConstructor
):
    _available_types = "text", "photo", "audio"

    def __init__(
            self,
            *,
            unique: bool = False,
            type_: Literal["text", "photo", "audio"] = "text",
            state: str | State | None = None,
            photo: str | FSInputFile | None = None,
            voice: str | FSInputFile | None = None,
            text_map: list[DataTextWidget | TextWidget] | None = None,
            keyboard_map: list[list[ButtonWidget]] | None = None,
            backable: bool = True,
            back_text: str = Emoji.BACK,
            left_text: str = Emoji.LEFT,
            left_mark: str = "",
            right_text: str = Emoji.RIGHT,
            right_mark: str = "",
            size_page: int = 10,
            buttons_per_line: int = 1,
            page: int = 0,
            data: list[ButtonWidget] = None,
    ):
        """
        :param unique: True mean no additional layers per chat
        :param type_: type message in telegram
        :param state: User state when active that window
        :param photo: will be show when active that window and type set as photo
        :param voice: will be show when active that window and type set as voice
        :param text_map: struct with text widgets
        :param keyboard_map: struct with button widgets
        :param backable: auto-adding back button with prepared handler
        :param back_text: text in back button
        :param left_text: text in left button
        :param left_mark: mark in left button
        :param right_text: text in right button
        :param right_mark: mark in right button
        :param size_page: quantity buttons per page
        :param page: start page number
        :param data: ButtonWidget array, will be parsed and if size_page > len(data) will be auto-added pagination
        """
        TextMarkupConstructor.__init__(self, text_map)
        KeyboardMarkupConstructor.__init__(self, keyboard_map)
        self.unique = unique
        self.back_inited = False
        self.inited_pagination = False
        self.data = [] if data is None else data
        self._size_page = size_page
        self.buttons_per_line = buttons_per_line
        self._partitioned_data = self.split(size_page, self.data)
        self.backable = backable
        self.page = page
        self.type = type_
        self.state = state
        self._photo = photo
        self._voice = voice
        self.left = ButtonWidget(text=left_text, mark=left_mark, sep="", callback_data="flip_left")
        self.right = ButtonWidget(text=right_text, mark=right_mark, sep="", callback_data="flip_right")
        self.back = ButtonWidget(text=back_text, callback_data="back")
        if self.type not in self._available_types:
            raise ValueError(f"Available type is {self._available_types} not {self.type}")

    @property
    def partitioned_data(self) -> List[Any]:
        return self._partitioned_data[self.page % len(self._partitioned_data)]

    @partitioned_data.setter
    def partitioned_data(self, partitioned_data: List[Any]):
        self._partitioned_data[self.page % len(self._partitioned_data)] = partitioned_data

    def init_pagination(self):
        if len(self._partitioned_data) > 1:
            self.add_buttons_in_new_row(self.left, self.right)
            self.inited_pagination = True

    def init_control(self):
        if self.backable:
            self.add_buttons_in_new_row(self.back)
            self.back_inited = True

    def reset(self):
        self.text_map = []
        self.keyboard_map = [[]]
        self.back_inited = False
        self.inited_pagination = False

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


class Info(WindowBuilder):
    def __init__(
        self,
        text: str,
        back_text: str = "Ok",
    ):
        super().__init__(back_text=back_text)
        self.add_texts_rows(TextWidget(text=text))


class Temp(WindowBuilder):
    def __init__(
        self,
        text: str = f"{Emoji.HOURGLASS_START} Processing...",
    ):
        super().__init__(backable=False)
        self.add_texts_rows(TextWidget(text=text))


class Input(WindowBuilder):
    def __init__(
        self,
        prompt: str,
        state: State | str,
        back_text: str = f"{Emoji.DENIAL} Cancel",
    ):
        super().__init__(state=state, back_text=back_text)
        self.add_texts_rows(TextWidget(text=prompt))


class Conform(WindowBuilder):
    def __init__(
        self,
        prompt: str,
        yes_callback_data: str | CallbackData,
        *,
        no_callback_data: str | CallbackData = "back",
        yes_text: str = f"{Emoji.OK} Yes",
        no_text: str = f"{Emoji.DENIAL} No",
    ):
        super().__init__(back_text=no_text, backable=False)
        self.add_texts_rows(TextWidget(text=prompt))
        self.add_buttons_in_new_row(
            ButtonWidget(text=yes_text, callback_data=yes_callback_data),
            ButtonWidget(text=no_text, callback_data=no_callback_data)
        )
