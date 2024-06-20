from base64 import b64decode, b64encode
from os import getenv
from math import ceil
from pickle import dumps, loads
from typing import Union, Any, List, Dict, Hashable, Set

from dotenv import find_dotenv, load_dotenv
from redis import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, ExpiryT, AbsExpiryT


load_dotenv(find_dotenv())


class Emoji:
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
        percent = ceil(float_fraction * 10)
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

    def __init__(self, id_: str = ""):
        self._id_ = id_

    def _get(self, key: str, default: Any | None = None):
        try:
            value = self.STORAGE.get(f"{key}:{self._id_}")
        except (AttributeError, ModuleNotFoundError, Exception):
            print(f"Impossible restore broken deserialized data\nKey: {key}")
            self._set(key, default)
            return default
        if value is None:
            return default
        return value

    def _set(self, key: str, value: Any):
        self.STORAGE.set(f"{key}:{self._id_}", value)


class ImmuneDict(Storage):
    def __init__(self, dict_name: str = "common_dict"):
        super().__init__(dict_name)

    @property
    def dict(self) -> Dict[Hashable, Any]:
        return self._get(self._id_, {})

    def __getitem__(self, item: Hashable):
        return self.dict.get(item)

    @dict.setter
    def dict(self, dict_: Dict[Hashable, Any]):
        self._set(self._id_, dict_)

    def __setitem__(self, key: Hashable, value: Any):
        dict_ = self.dict
        dict_[key] = value
        self.dict = dict_

    def destroy(self):
        self.dict = None


class ImmuneList(Storage):
    def __init__(self, list_name: str = "common_list"):
        super().__init__(list_name)

    @property
    def _list(self) -> List[Any]:
        return self._get(self._id_, [])

    def __getitem__(self, index: int):
        try:
            return self._list[index]
        except IndexError:
            return

    @_list.setter
    def _list(self, list_: List[Any]):
        self._set(self._id_, list_)

    def __setitem__(self, index: int, value: Any):
        list_ = self._list
        list_[index] = value
        self._list = list_

    def append(self, item: Any):
        list_ = self._list
        list_.append(item)
        self._list = list_

    def extend(self, *items: Any):
        list_ = self._list
        list_.extend(items)
        self._list = list_

    def pop_last(self):
        list_ = self._list
        if not list_:
            return
        item = list_.pop()
        self._list = list_
        return item

    def reset(self, item: Any):
        self._list = [item]

    def remove(self, message_id: int):
        list_ = self._list
        try:
            list_.remove(message_id)
            self._list = list_
            return True
        except ValueError:
            return False

    def destroy(self):
        self._list = None


class ImmuneSet(Storage):
    def __init__(self, set_name: str = "common_set"):
        super().__init__(set_name)

    @property
    def set(self) -> Set:
        return self._get(self._id_, set())

    def add(self, item: Any):
        set_ = self.set
        set_.add(item)
        self.set = set_

    @set.setter
    def set(self, set_: Set):
        self._set(self._id_, set_)

    def destroy(self):
        self.set = None
