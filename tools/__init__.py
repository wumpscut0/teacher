from asyncio import to_thread
from os import getenv
from math import ceil
from pickle import dumps, loads
from typing import Union, Any, Iterable

from dotenv import find_dotenv, load_dotenv
from redis.asyncio import Redis
from redis.commands.core import ResponseT
from redis.typing import KeyT, ExpiryT, AbsExpiryT

from tools.loggers import debug_tools, info_tools, errors_tools

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
    PHOTO = "🖼️"
    CLOCK = "🕒"
    AUDIO = "🔊"
    FROG = "🐸"
    HOURGLASS_START = "⏳"
    HOURGLASS_END = "⌛️"
    MOYAI = "🗿"
    CLOWN = "🤡"
    WHEELCHAIR = "♿️"
    COLORS = "🎨"
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
    CANDLE = "🕯️"
    TAG = "🏷️"
    TICK = "✔️"
    SYNTH_MUSCLE = "🦾"
    CONFETTI = "🎊"
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
    FOX = "🦊"
    DOG = "🐶"
    CAT = "🐱"
    LION = "🦁"
    TIGER = "🐯"
    PIG = "🐷"
    COW = "🐮"
    MOUSE = "🐭"
    PANDA = "🐼"
    RABBIT = "🐰"
    CHICKEN = "🐥"
    BEAR = "🐻"
    HOME = "🏠"
    WOMAN_MAN = "👫"
    CHILD = "👶"
    OPEN_BOOK = "📖"
    BOX = "📦"
    DNA = "🧬"
    FLASK = "🧪"
    DARK_START = "★"
    BROKEN_ROSE = "🥀"
    HYGEUM = "⚕"
    PENCIL_2 = "✎"
    WRITING_HAND = "✍"
    UNIVERSE = "🌌"
    TALKING_HEAD = "🗣"
    ABCD = "🔠"
    CLIPS = "🖇️"
    THOUGHT_BABBLE = "💬"
    PLAY = "▶"
    WEB = "🕸️"
    GIFT = "🎁"
    MAGIC_SPHERE = "🔮"
    ALCHEMY = "⚗️"
    VIOLET_ATOM = "⚛️"
    SPIRAL = "🌀"
    PUZZLE = "🧩"
    PICTURE_2 = "🖼"
    WAVE = "🌊"
    BOOKS_STACK = "📚"
    CHAINS = "⛓️"
    SQUARE_ACADEMIC_CAP = "🎓"
    BIOHAZARD = "☣"
    SCALES = "⚖"
    CHAIN_SEPARATOR = "⫘⫘⫘"
    CUBE = "💠"


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


class CustomRedis(Redis):
    async def set(
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
        return await super().set(
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

    async def get(self, name: KeyT) -> ResponseT:
        result: Any = await super().get(name)
        if result is not None:
            return await to_thread(loads, result)

    async def setex(self, name: KeyT, time: ExpiryT, value: Any) -> ResponseT:
        return await super().setex(
            name,
            time,
            dumps(value),
        )

    async def getex(
        self,
        name: KeyT,
        ex: Union[ExpiryT, None] = None,
        px: Union[ExpiryT, None] = None,
        exat: Union[AbsExpiryT, None] = None,
        pxat: Union[AbsExpiryT, None] = None,
        persist: bool = False,
    ) -> ResponseT:
        result: Any = await super().getex(name, ex, px, exat, pxat, persist)
        if result is not None:
            return await to_thread(loads, result)


class Storage:
    CLIENT = CustomRedis(
        host=getenv("REDIS_HOST"), port=int(getenv("REDIS_PORT")), db=1
    )

    def __init__(self, key: str, default: Any):
        self._key = key
        self._default = default

    async def get(self):
        try:
            value = await self.CLIENT.get(self._key)
            debug_tools.debug(f"GET key: {self._key} -> value: {value}")
        except (AttributeError, ModuleNotFoundError, Exception):
            errors_tools.error(f"Impossible restore broken deserialized data\nKey: {self._key}")
            await self.set(self._default)
            return self._default
        if value is None:
            return self._default
        return value

    async def set(self, value: Any, save_data_in_log: bool = True):
        if save_data_in_log:
            debug_tools.debug(f"SET {self._key} -> value: {value}")
        else:
            debug_tools.debug(f"SET key: {self._key} -> value: {value}")
        await self.CLIENT.set(self._key, value)

    async def destroy(self, save_data_in_log: bool = True):
        if save_data_in_log:
            data = await self.CLIENT.get(self._key)
            await self.CLIENT.set(self._key, None)
            info_tools.info(f"Data: {data} removed from key: {self._key} ")
        else:
            await self.CLIENT.set(self._key, None)
            info_tools.info(f"Data by key: {self._key} destroyed")


class DictStorage(Storage):
    def __init__(self, id_: str):
        super().__init__(id_, {})

    async def get_value_by_key(self, key: str, default: Any | None = None):
        try:
            return (await self.get())[key]
        except KeyError:
            return default

    async def set_value_by_key(self, key: str, value):
        user_storage = await self.get()
        user_storage[key] = value
        await self.set(user_storage)

    async def destroy_key(self, key: str):
        try:
            user_storage = await self.get()
            user_storage.pop(key)
            await self.set(user_storage)
            return True
        except KeyError:
            return False


class ListStorage(Storage):
    def __init__(self, key: str):
        super().__init__(key, [])

    async def append(self, item: Any):
        list_ = await self.get()
        list_.append(item)
        await self.set(list_)

    async def extend(self, items: Iterable):
        list_ = await self.get()
        list_.extend(items)
        await self.set(list_)

    async def pop_last(self):
        list_ = await self.get()
        if not list_:
            return
        item = list_.pop()
        await self.set(list_)
        return item

    async def reset(self, item: Any):
        await self.set([item])

    async def remove(self, message_id: int):
        list_ = await self.get()
        try:
            list_.remove(message_id)
            await self.set(list_)
            return True
        except ValueError:
            return False

    async def set_last(self, item: Any):
        list_ = await self.get()
        if not list_:
            await self.reset(item)
        else:
            list_[-1] = item
            await self.set(list_)

    async def get_last(self):
        try:
            return (await self.get())[-1]
        except IndexError:
            return

    async def get_all_except_last(self):
        return (await self.get())[:-1]
