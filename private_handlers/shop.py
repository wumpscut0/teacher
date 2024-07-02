from asyncio import gather
from random import shuffle

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from api import SuperEnglishDictionary
from core.markups import Info, Conform

from core import BotControl, Routers
from private_markups import English, InspectEnglishRun, BanWordCallbackData, knowledge_as_progress_string
from private_markups.shop import Shop
from tools import Emoji

private_shop_router = Routers.private()


@private_shop_router.callback_query(F.data == "init_shop")
async def init_shop(callback: CallbackQuery, bot_control: BotControl):
    shop = await bot_control.bot_storage.get_value_by_key("shop", {})
    if not shop:
        await bot_control.append(Info(f"Nothing to show {Emoji.BAN}"))
        return

    collection = await bot_control.user_storage.get_value_by_key("collection", set())

    shop = {k: v for k, v in shop.items() if k not in collection}
    if not shop:
        await bot_control.append(Info(f"Shop is empty {Emoji.WEB}"))
        return

    shop = Shop(shop)

    dna = await bot_control.user_storage.get_value_by_key("english:total_dna", {})
    cube = await bot_control.user_storage.get_value_by_key("english:keys", {})
    stars = 0

    user_knowledge = await bot_control.user_storage.get_value_by_key("english:knowledge", {})
    for word in await bot_control.bot_storage.get_value_by_key("words", set()):
        data = await SuperEnglishDictionary.extract_data(word)
        if data["pos"]:
            knowledge_size = len(SuperEnglishDictionary.build_knowledge_schema(data))
            stars += knowledge_as_progress_string(user_knowledge.get(word, {}), knowledge_size).count(Emoji.STAR)

    shop.balance_display(dna, cube, stars)
    await bot_control.append(shop)

