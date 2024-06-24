from aiogram import F
from aiogram.types import CallbackQuery

from core import BotControl, Routers
from core.markups import Info
from group_markups import EditEnglishRun, WordTickCallbackData, AcceptOffer
from tools import Emoji

party_router = Routers.group()


@party_router.callback_query(F.data == "exit")
async def get_offer(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.clear_chat(force=True)


@party_router.callback_query(F.data == "get_offer")
async def get_offer(callback: CallbackQuery, bot_control: BotControl):
    try:
        offer = bot_control.bot_storage["offer"]
    except KeyError:
        offer = []
    if not offer:
        await bot_control.extend(Info(f"No offers so far {Emoji.CRYING_CAT}"))
        return

    await bot_control.append(AcceptOffer(offer))


@party_router.callback_query(F.data == "edit_english_run")
async def edit_english_run(callback: CallbackQuery, bot_control: BotControl):
    try:
        words = bot_control.bot_storage["words"]
    except KeyError:
        words = []

    if not words:
        await bot_control.extend(Info(f"English run is empty {Emoji.CRYING_CAT}"))
        return

    await bot_control.extend(EditEnglishRun(words))


@party_router.callback_query(WordTickCallbackData.filter())
async def marking_words(callback: CallbackQuery, callback_data: WordTickCallbackData, bot_control: BotControl):
    markup = bot_control.current
    if markup.partitioned_data[callback_data.index].mark == Emoji.OK:
        markup.partitioned_data[callback_data.index].mark = Emoji.DENIAL
    else:
        markup.partitioned_data[callback_data.index].mark = Emoji.OK

    await bot_control.set_current(markup)


@party_router.callback_query(F.data == "accept_edit_english_run")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    markup = bot_control.current
    words = bot_control.bot_storage["words"]
    for word in (word.text for word in markup.data if word.mark == Emoji.DENIAL):
        words.remove(word)
    bot_control.bot_storage["words"] = words
    await bot_control.back()


@party_router.callback_query(F.data == "accept_offer")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    markup = bot_control.current
    try:
        words = bot_control.bot_storage["words"]
    except KeyError:
        words = []

    words.extend((word.text for word in markup.data if word.mark == Emoji.OK))
    bot_control.bot_storage["words"] = words
    bot_control.bot_storage["offer"] = []
    await bot_control.back()


@party_router.callback_query(F.data == "drop_offer")
async def drop_offer(callback: CallbackQuery, bot_control: BotControl):
    bot_control.bot_storage["offer"] = []
    await bot_control.back()
