from aiogram import F
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery

from core.markups import Info, Conform, WindowBuilder, ButtonWidget

from core import BotControl, Routers
from models.shop import Shop, BuyingContentCallbackData


from tools import Emoji

private_shop_router = Routers.private()


@private_shop_router.callback_query(F.data == "shop")
async def open_shop(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.append(Shop("buy"))


@private_shop_router.callback_query(BuyingContentCallbackData.filter())
async def buy(callback: CallbackQuery, callback_data: BuyingContentCallbackData, bot_control: BotControl):
    shop: Shop = await bot_control.get_current()
    shop_data = await bot_control.bot_storage.get_value_by_key("shop")
    item = shop_data[callback_data.name]
    widget = "\n"
    for currency, cost in item["cost"].items():
        if int(shop.temp_balance[currency]) < cost:
            await bot_control.append(Info(f"Now enough funds {Emoji.CRYING_CAT}"))
            return
        widget += f"{currency} {cost}\n"

    await bot_control.append(Conform(f"Conform buying {callback_data.name}?{widget}",
                                     yes_callback_data=f"buying:{callback_data.name}"))


@private_shop_router.callback_query(F.data.startswith("buying:"))
async def buying(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.pop_last()
    shop: Shop = await bot_control.get_current()

    _, name = callback.data.split(":")
    await shop.buying(bot_control, name)

    await bot_control.set_current(shop)


class ShowItemCallbackData(CallbackData, prefix="show_item"):
    name: str


@private_shop_router.callback_query(F.data == "collection")
async def collection_(callback: CallbackQuery, bot_control: BotControl):
    collection_data = await bot_control.user_storage.get_value_by_key("collection", {})
    if not collection_data:
        await bot_control.append(Info(f"No items so far {Emoji.WEB}"))

    buttons = []
    for name, content in collection_data.items():
        buttons.append(ButtonWidget(text=name, callback_data=ShowItemCallbackData(name=name)))
    collection = WindowBuilder(
        paginated_buttons=buttons,
        buttons_per_line=3,
        buttons_per_page=30
    )
    await bot_control.append(collection)


@private_shop_router.callback_query(ShowItemCallbackData.filter())
async def collection_(callback: CallbackQuery, callback_data: ShowItemCallbackData, bot_control: BotControl):
    collection_data = await bot_control.user_storage.get_value_by_key("collection", {})
    item_data = collection_data[callback_data.name]
    item = WindowBuilder(
        type_=item_data["type"],
    )
    if item_data["type"] == "photo":
        item.photo = item_data["content"]
    else:
        item.voice = item_data["content"]

    await bot_control.append(item)
