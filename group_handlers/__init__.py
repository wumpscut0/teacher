from aiogram import F
from aiogram.types import Message, CallbackQuery

from cache import EnglishRunStorage, WordTickCallbackData
from core import BotControl, Info, Routers, ButtonWidget, BotCommands
from database.queries import insert_new_words, select_words
from core.tools import Emoji
from group_markups import EditEnglishRun

party_router = Routers.group()


@party_router.message(BotCommands.start())
async def start(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.look_around()


@party_router.message(BotCommands.exit())
async def exit_(message: CallbackQuery, bot_control: BotControl):
    await bot_control.sleep()


@party_router.callback_query(F.data == "get_offer")
async def get_offer(message: Message, bot_control: BotControl):
    storage = EnglishRunStorage()
    offer = storage.offer
    if not offer:
        await bot_control.dig(Info(f"No offers so far {Emoji.CRYING_CAT}"))
        return

    storage.current_edit_is_offer = True
    storage.edit = offer
    await bot_control.dig(EditEnglishRun())


@party_router.callback_query(F.data == "edit_english_run")
async def edit_english_run(callback: CallbackQuery, bot_control: BotControl):
    storage = EnglishRunStorage()
    words = [ButtonWidget(
        mark=Emoji.OK,
        text=f"{word.eng}:{", ".join(word.translate)}",
        callback_data=WordTickCallbackData(index=i))
        for i, word in enumerate(await select_words())
    ]
    if not words:
        await bot_control.dig(Info(f"English run is empty {Emoji.CRYING_CAT}"))
        return

    storage.current_edit_is_offer = False
    storage.edit = words
    await bot_control._update_text_message(EditEnglishRun)


@party_router.callback_query(F.data == "flip_left_edit")
async def flip_left_offer(callback: CallbackQuery, bot_control: BotControl):
    EnglishRunStorage().flip_left_edit()
    await bot_control._update_text_message(EditEnglishRun)


@party_router.callback_query(F.data == "flip_right_edit")
async def flip_right_offer(callback: CallbackQuery, bot_control: BotControl):
    EnglishRunStorage().flip_right_edit()
    await bot_control._update_text_message(EditEnglishRun)


@party_router.callback_query(WordTickCallbackData.filter())
async def marking_words(callback: CallbackQuery, callback_data: WordTickCallbackData, bot_control: BotControl):
    storage = EnglishRunStorage()
    offer_copy = storage.edit
    if offer_copy[callback_data.index].mark == Emoji.OK:
        offer_copy[callback_data.index].mark = Emoji.DENIAL
    else:
        offer_copy[callback_data.index].mark = Emoji.OK
    storage.edit = offer_copy

    await bot_control._update_text_message(EditEnglishRun)


@party_router.callback_query(F.data == "update_english_run")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    EnglishRunStorage().offer = []
    await insert_new_words()
    await bot_control._look_around()


@party_router.callback_query(F.data == "rewrite_english_run")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    await insert_new_words(rewrite=True)
    await bot_control._look_around()


@party_router.callback_query(F.data == "drop_offer")
async def drop_offer(callback: CallbackQuery, bot_control: BotControl, ):
    EnglishRunStorage().offer = []
    await bot_control._look_around()


