from typing import List, Literal, Any, Iterable, TypeVar, Tuple

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
    _no_photo = "AgACAgIAAx0Cf42o9wACA1pmg-PfOMzziFicxV7itfg34ZbwawACsN8xG3rTIEj3ZE18dVVwmQEAAwIAA20AAzUE"
    _no_audio = 'CQACAgIAAx0Cf42o9wACA11mg-WsuShax7eXPExHO9EEbPg1EgACrFIAAnrTIEiM_mvZKw3k1TUE'

    def __init__(
            self,
            *,
            init_schema: Tuple[str] = (
                "frozen_text",
                "paginated_buttons",
                "frozen_buttons",
                "pagination",
                "back"
            ),
            unique: bool = False,
            type_: Literal["text", "photo", "audio"] = "text",
            state: str | State | None = None,
            photo: str | FSInputFile | None = None,
            voice: str | FSInputFile | None = None,
            text_map: list[DataTextWidget | TextWidget] | None = None,
            keyboard_map: list[list[ButtonWidget]] | None = None,
            frozen_buttons_map: list[list[ButtonWidget]] | None = None,
            paginated_buttons: list[ButtonWidget] = None,
            frozen_text_map: list[TextWidget | DataTextWidget] | None = None,
            auto_back: bool = True,
            back_callback_data: str = "back",
            back_text: str = Emoji.BACK,
            left_text: str = Emoji.LEFT,
            left_mark: str = "",
            right_text: str = Emoji.RIGHT,
            right_mark: str = "",
            buttons_per_page: int = 10,
            buttons_per_line: int = 1,
            page: int = 0,
    ):
        TextMarkupConstructor.__init__(self, text_map)
        KeyboardMarkupConstructor.__init__(self, keyboard_map)
        self._init_map = {
            "frozen_text": self._init_frozen_text_map,
            "paginated_buttons": self._init_paginated_buttons,
            "frozen_buttons": self._init_frozen_buttons_map,
            "pagination": self._init_pagination,
            "back": self._init_back,
        }
        self.init_schema = init_schema
        self.frozen_text_map = frozen_text_map
        self.frozen_buttons_map = frozen_buttons_map
        self.unique = unique

        self._frozen_text_map_inited = False
        self._paginated_buttons_inited = False
        self._frozen_buttons_map_inited = False
        self._pagination_inited = False
        self._back_inited = False

        self.paginated_buttons = [] if paginated_buttons is None else paginated_buttons
        self._size_page = buttons_per_page
        self.buttons_per_line = buttons_per_line
        self.backable = auto_back
        self.page = page
        self.type = type_
        self.state = state
        self._photo = photo
        self._voice = voice
        self.left = ButtonWidget(text=left_text, mark=left_mark, sep="", callback_data="flip_left")
        self.right = ButtonWidget(text=right_text, mark=right_mark, sep="", callback_data="flip_right")
        self.back = ButtonWidget(text=back_text, callback_data=back_callback_data)
        if self.type not in self._available_types:
            raise ValueError(f"Available type is {self._available_types} not {self.type}")

    @property
    def partitioned_data(self) -> List[Any]:
        partitioned_data = self.split(self._size_page, self.paginated_buttons)
        return partitioned_data[self.page % len(partitioned_data)]

    def init(self):
        for display_name in self.init_schema:
            self._init_map[display_name]()

    def _init_frozen_text_map(self):
        if not self._frozen_text_map_inited and self.frozen_text_map:
            self.add_texts_rows(*self.frozen_text_map)
            self._frozen_text_map_inited = True

    def _init_paginated_buttons(self):
        if not self._paginated_buttons_inited and self.partitioned_data:
            for row in self.split(self.buttons_per_line, self.partitioned_data):
                self.add_buttons_in_new_row(*row)
            self._paginated_buttons_inited = True

    def _init_frozen_buttons_map(self):
        if not self._frozen_buttons_map_inited and self.frozen_buttons_map:
            for row in self.frozen_buttons_map:
                self.add_buttons_in_new_row(*row)
            self._frozen_buttons_map_inited = True

    def _init_pagination(self):
        if not self._pagination_inited and len(self.split(self._size_page, self.paginated_buttons)) > 1:
            self.add_buttons_in_new_row(self.left, self.right)
            self._pagination_inited = True

    def _init_back(self):
        if not self._back_inited and self.backable:
            self.add_buttons_in_new_row(self.back)
            self._back_inited = True

    def reset(self):
        self.text_map = []
        self.keyboard_map = [[]]
        self._frozen_text_map_inited = False
        self._paginated_buttons_inited = False
        self._frozen_buttons_map_inited = False
        self._pagination_inited = False
        self._back_inited = False

    @property
    def voice(self):
        if self._voice is None:
            return self._no_audio
        return self._voice

    @voice.setter
    def voice(self, voice: str | FSInputFile):
        self._voice = voice

    @property
    def photo(self):
        if not self._photo:
            return self._no_photo
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

    def back_as_cancel(self):
        self.back.text = f"{Emoji.DENIAL} Cancel"
        self.back.callback_data = "back"


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
        super().__init__(auto_back=False)
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
        super().__init__(back_text=no_text, auto_back=False)
        self.add_texts_rows(TextWidget(text=prompt))
        self.add_buttons_in_new_row(
            ButtonWidget(text=yes_text, callback_data=yes_callback_data),
            ButtonWidget(text=no_text, callback_data=no_callback_data)
        )
