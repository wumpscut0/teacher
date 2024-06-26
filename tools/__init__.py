from base64 import b64decode, b64encode
from os import getenv
from math import ceil
from pickle import dumps, loads
from typing import Union, Any, List, Set, Iterable

from dotenv import find_dotenv, load_dotenv
from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, ExpiryT, AbsExpiryT


load_dotenv(find_dotenv())


class Emoji:
    STAR = "⭐"
    LAMP = "💡"
    OK = "✅"
    DENIAL = "❌"
    INFO = "ℹ"
    BACK = "⬇"
    KEY = "🔑"
    DOOR = "🚪"
    BRAIN = "🧠"
    MEGAPHONE = "📢"
    SHINE_STAR = "🌟"
    WARNING = "⚠"
    SHIELD = "🛡"
    CYCLE = "🔄"
    BELL = "🔔"
    NOT_BELL = "🔕"
    EYE = "👁"
    SPROUT = "🌱"
    DIAGRAM = "📊"
    BULB = "💡"
    GEAR = "⚙"
    EMAIL = "📧"
    LOCK_AND_KEY = "🔐"
    PLUS = "➕"
    UP = "🆙"
    SKIP = "⏭️"
    GREEN_BIG_SQUARE = "🟩"
    GREY_BIG_SQUARE = "⬜️"
    RED_QUESTION = "❓"
    GREY_QUESTION = "❔"
    BAN = "🚫"
    GREEN_CIRCLE = "🟢"
    YELLOW_CIRCLE = "🟡"
    ORANGE_CIRCLE = "🟠"
    RED_CIRCLE = "🔴"
    FLAG_FINISH = "🏁"
    DART = "🎯"
    REPORT = "🧾"
    LIST_WITH_PENCIL = "📝"
    NEW = "🆕"
    TROPHY = "🏆"
    CLOCK = "🕒"
    FROG = "🐸"
    HOURGLASS_START = "⏳"
    HOURGLASS_END = "⌛️"
    MOYAI = "🗿"
    CLOWN = "🤡"
    WHEELCHAIR = "♿️"
    CRYING_CAT = "😿"
    LEFT = "⬅"
    RIGHT = "➡"
    BUG = "🪲"
    INCOMING_ENVELOPE = "📨"
    UNLOCK = "🔓"
    PENCIL = "✏️"
    BROKEN_HEARTH = "💔"
    ZZZ = "💤"
    ZAP = "⚡️"
    YUM = "😋"
    WATCH = "⌚️"
    DECIDUOUS_TREE = "🌳"
    DROPLET = "💧"
    FALLEN_LEAF = "🍂"
    GLOBE_WITH_MERIDIANS = "🌐"
    SMALL_RED_TRIANGLE_DOWN = "🔻"
    GLASS_OF_MILK = "🥛"
    FIVE = "5️⃣"
    SIX = "6️⃣"
    SEVEN = "7️⃣"
    EIGHT = "8️⃣"
    NINE = "9️⃣"
    TEN = "🔟"
    KNIFE = "🔪"
    FIRE = "🔥"
    BULLET = "⁍"
    SIGHT = "⊹"
    GUN = "▄︻テ══━一"
    FLOPPY_DISC = "💾"
    TICK = "✔️"
    SYNTH_MUSCLE = "🦾"
    WHITE_BLACK_START = "✮"
    ABYSS = "🕳️"
    DIAGRAM_TOP = "📈"
    ONE = "1️⃣"
    TWO = "2️⃣"
    THERE = "3️⃣"
    FOUR = "4️⃣"
    CROWN = "🜲"
    MONKEY = "🦧"
    MUSCLE = "💪🏼"
    ANIMALS = '🦊🐶🐱🦁🐯🐷🐮🐭🐹🐼🐨🐰🐻🦉🐥🐸🐙🦭'
    HOME = "🏠"
    WOMAN_MAN = "👫"
    CHILD = "👶"
    OPEN_BOOK = "📖"
    BOX = "📦"
    DNA = "🧬"
    FLASK = "🧪"
    BROKEN_ROSE = "🥀"
    HYGEUM = "⚕"
    WRITING_HAND = "✍"
    UNIVERSE = "🌌"
    TALKING_HEAD = "🗣"
    ABCD = "🔠"
    CLIPS = "🖇️"
    THOUGHT_BABBLE = "💬"
    PLAY = "▶"
    ALCHEMY = "⚗️"
    VIOLET_ATOM = "⚛️"
    SPIRAL = "🌀"
    PUZZLE = "🧩"
    WAVE = "🌊"
    BOOKS_STACK = "📚"
    SQUARE_ACADEMIC_CAP = "🎓"
    BIOHAZARD = "☣"
    BIOHAZARD_2 = "☣️"
    BIOHAZARD_3 = "☣"
    SCALES = "⚖"
    SCALES_2 = "⚖️"
    DOWN_ARROW = "⬇"


def create_progress_text(
    numerator: int,
    denominator: int,
    *,
    progress_element: str = Emoji.GREEN_BIG_SQUARE,
    remaining_element: str = Emoji.GREY_BIG_SQUARE,
    length_widget: int = 10,
    show_digits: bool = True,
):
    if numerator > denominator:
        percent = 100
        progress = progress_element * length_widget
    else:
        float_fraction = numerator / denominator * length_widget
        percent = ceil(numerator / denominator * 100)
        fraction = ceil(float_fraction)
        grey_progress = (length_widget - fraction) * remaining_element
        green_progress = fraction * progress_element
        progress = green_progress + grey_progress

    if show_digits:
        return f"{progress} {percent}%"
    return progress


class SerializableMixin:
    async def serialize(self):
        return b64encode(dumps(self)).decode()


async def deserialize(sequence: str):
    return loads(b64decode(sequence.encode()))


class CustomRedis(Redis):
    def set(
        self,
        name: KeyT,
        value: Any,
        ex: Union[ExpiryT, None] = None,
        px: Union[ExpiryT, None] = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,
        get: bool = False,
        exat: Union[AbsExpiryT, None] = None,
        pxat: Union[AbsExpiryT, None] = None,
    ) -> ResponseT:
        return super().set(
            name,
            dumps(value),
            ex,
            px,
            nx,
            xx,
            keepttl,
            get,
            exat,
            pxat,
        )

    def get(self, name: KeyT) -> ResponseT:
        result: Any = super().get(name)
        if result is not None:
            return loads(result)

    def setex(self, name: KeyT, time: ExpiryT, value: Any) -> ResponseT:
        return super().setex(
            name,
            time,
            dumps(value),
        )

    def getex(
        self,
        name: KeyT,
        ex: Union[ExpiryT, None] = None,
        px: Union[ExpiryT, None] = None,
        exat: Union[AbsExpiryT, None] = None,
        pxat: Union[AbsExpiryT, None] = None,
        persist: bool = False,
    ) -> ResponseT:
        result: Any = super().getex(name, ex, px, exat, pxat, persist)
        if result is not None:
            return loads(result)


class Storage:
    STORAGE = CustomRedis(
        host=getenv("REDIS_HOST"), port=int(getenv("REDIS_PORT")), db=1
    )

    def __init__(self, key: str = ""):
        self._key = key

    def _get(self, default: Any | None = None):
        try:
            value = self.STORAGE.get(self._key)
            print(f"GET key: {self._key} ; value: {value}")
        except (AttributeError, ModuleNotFoundError, Exception):
            print(f"Impossible restore broken deserialized data\nKey: {self._key}")
            self._set(default)
            return default
        if value is None:
            return default
        return value

    def _set(self, value: Any):
        # print(f"SET key: {self._key} ; value: {value}")
        self.STORAGE.set(self._key, value)

    def destroy(self):
        self.STORAGE.set(self._key, None)


class ImmuneDict(Storage):
    def __init__(self, id_: str | int = "common_dict"):
        super().__init__(id_)

    def __getitem__(self, key: str):
        return self._get({})[key]

    def __setitem__(self, key: str, value: Any):
        dict_ = self._get({})
        dict_[key] = value
        self._set(dict_)

    def get(self, key: str, default: Any | None = None):
        try:
            return self._get({})[key]
        except KeyError:
            return default


class ImmuneList(Storage):
    def __init__(self, id_: str | int = "common_list"):
        super().__init__(id_)

    @property
    def list(self) -> List[Any]:
        return self._get([])

    def __getitem__(self, index: int):
        return self.list[index]

    @list.setter
    def list(self, list_: List[Any]):
        self._set(list_)

    def __setitem__(self, index: int, value: Any):
        list_ = self.list
        list_[index] = value
        self.list = list_

    def append(self, item: Any):
        list_ = self.list
        list_.append(item)
        self.list = list_

    def extend(self, items: Iterable):
        list_ = self.list
        list_.extend(items)
        self.list = list_

    def pop_last(self):
        list_ = self.list
        if not list_:
            return
        item = list_.pop()
        self.list = list_
        return item

    def reset(self, item: Any):
        self.list = [item]

    def remove(self, message_id: int):
        list_ = self.list
        try:
            list_.remove(message_id)
            self.list = list_
            return True
        except ValueError:
            return False


class ImmuneSet(Storage):
    def __init__(self, id_: str | int = "common_set"):
        super().__init__(id_)

    @property
    def set(self) -> Set:
        return self._get(set())

    def add(self, item: Any):
        set_ = self.set
        set_.add(item)
        self.set = set_

    @set.setter
    def set(self, set_: Set):
        self._set(set_)
