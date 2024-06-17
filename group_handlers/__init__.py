from aiogram import F
from aiogram.types import Message, CallbackQuery

from cache import Offer
from core import BotControl, Routers, BotCommands
from core.markups import Info
from database.models import WordModel
from database.queries import insert_new_words, select_words, delete_words
from core.tools import Emoji
from group_markups import EditEnglishRun, WordTickCallbackData, AcceptOffer

party_router = Routers.group()


@party_router.message(BotCommands.start)
async def start(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.look_around()


@party_router.message(BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.sleep()


@party_router.callback_query(F.data == "exit")
async def exit_(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.sleep()


@party_router.callback_query(F.data == "get_offer")
async def get_offer(message: Message, bot_control: BotControl):
    offer = Offer().offer
    if not offer:
        await bot_control.dig(Info(f"No offers so far {Emoji.CRYING_CAT}"))
        return

    await bot_control.dig(AcceptOffer(offer))


@party_router.callback_query(F.data == "edit_english_run")
async def edit_english_run(callback: CallbackQuery, bot_control: BotControl):
    words = await select_words()
    if not words:
        await bot_control.dig(Info(f"English run is empty {Emoji.CRYING_CAT}"))
        return

    await bot_control.dig(EditEnglishRun(words))


@party_router.callback_query(WordTickCallbackData.filter())
async def marking_words(callback: CallbackQuery, callback_data: WordTickCallbackData, bot_control: BotControl):
    current_point = await bot_control.get_current_point()
    if current_point.data[callback_data.index].mark == Emoji.OK:
        current_point.data[callback_data.index].mark = Emoji.DENIAL
    else:
        current_point.data[callback_data.index].mark = Emoji.OK
    await bot_control.dream(current_point)


@party_router.callback_query(F.data == "accept_edit_english_run")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    current_point = await bot_control.get_current_point()
    await delete_words(*(word.only_text.split(":")[0] for word in current_point.data if word.mark == Emoji.DENIAL))
    await bot_control.bury()


@party_router.callback_query(F.data == "accept_offer")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    current_point = await bot_control.get_current_point()
    await insert_new_words(*(WordModel(
        eng=word.only_text.split(":")[0],
        translate=word.only_text.split(":")[1].split(", "))
        for word in current_point.data if word.mark == Emoji.OK
    ))
    await bot_control.bury()
    Offer().offer = []


@party_router.callback_query(F.data == "drop_offer")
async def drop_offer(callback: CallbackQuery, bot_control: BotControl):
    Offer().offer = []
    await bot_control.bury()
