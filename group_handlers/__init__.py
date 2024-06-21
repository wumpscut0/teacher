from aiogram import F
from aiogram.types import CallbackQuery

from cache import Offer
from core import BotControl, Routers
from core.markups import Info
from database.queries import insert_new_words, select_words, delete_words
from group_markups import EditEnglishRun, WordTickCallbackData, AcceptOffer
from tools import Emoji

party_router = Routers.group()


@party_router.callback_query(F.data == "exit")
async def get_offer(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.clear_chat(force=True)


@party_router.callback_query(F.data == "get_offer")
async def get_offer(callback: CallbackQuery, bot_control: BotControl):
    offer = Offer().offer
    if not offer:
        await bot_control.extend(await Info(f"No offers so far {Emoji.CRYING_CAT}").update())
        return

    await bot_control.extend(await AcceptOffer(offer).update())


@party_router.callback_query(F.data == "edit_english_run")
async def edit_english_run(callback: CallbackQuery, bot_control: BotControl):
    words = await select_words()
    if not words:
        await bot_control.extend(await Info(f"English run is empty {Emoji.CRYING_CAT}").update())
        return

    await bot_control.extend(await EditEnglishRun(words).update())


@party_router.callback_query(WordTickCallbackData.filter())
async def marking_words(callback: CallbackQuery, callback_data: WordTickCallbackData, bot_control: BotControl):
    markup = bot_control.last
    if markup.data[callback_data.index].mark == Emoji.OK:
        markup.data[callback_data.index].mark = Emoji.DENIAL
    else:
        markup.data[callback_data.index].mark = Emoji.OK

    await bot_control.set_last(await markup.update())


@party_router.callback_query(F.data == "accept_edit_english_run")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    markup = bot_control.last
    await delete_words((word.only_text for word in markup.data if word.mark == Emoji.DENIAL))
    await bot_control.pop_last()


@party_router.callback_query(F.data == "accept_offer")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    markup = bot_control.last
    await insert_new_words((word.only_text for word in markup.data if word.mark == Emoji.OK))
    await bot_control.pop_last()
    Offer().destroy()


@party_router.callback_query(F.data == "drop_offer")
async def drop_offer(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.pop_last()
    Offer().destroy()
