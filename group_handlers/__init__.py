from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from alt_aiogram import BotControl, Info
from alt_aiogram.redis import OfferWordTickCallbackData, OfferStorage
from database.queries import insert_new_words
from markups import Offer
from tools import Emoji

party_router = Router()


@party_router.callback_query(F.data == "return_to_context")
async def return_to_context(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.return_to_context()


@party_router.message(F.text == "T")
async def start(message: Message, bot_control: BotControl):
    await bot_control.return_to_context()


@party_router.callback_query(F.data == "get_offer")
async def get_offer(message: Message, bot_control: BotControl):
    offer_storage = OfferStorage()
    offer = offer_storage.offer
    if not offer:
        await bot_control.update_text_message(Info, f"No offers so far {Emoji.CRYING_CAT}")
        return
    offer_storage.offer_copy = offer
    offer_storage.offer = []
    await bot_control.update_text_message(Offer)


@party_router.callback_query(F.data == "flip_left_offer")
async def flip_left_offer(callback: CallbackQuery, bot_control: BotControl):
    bot_control.tuurngaid.flip_left_offer()
    await bot_control.update_text_message(Offer)


@party_router.callback_query(F.data == "flip_right_offer")
async def flip_right_offer(callback: CallbackQuery, bot_control: BotControl):
    bot_control.tuurngaid.flip_right_offer()
    await bot_control.update_text_message(Offer)


@party_router.callback_query(OfferWordTickCallbackData.filter())
async def marking_words(callback: CallbackQuery, callback_data: OfferWordTickCallbackData, bot_control: BotControl):
    offer_copy = bot_control.tuurngaid.offer_copy
    if offer_copy[callback_data.index].mark == Emoji.TICK:
        offer_copy[callback_data.index].mark = Emoji.DENIAL
    else:
        offer_copy[callback_data.index].mark = Emoji.TICK

    await bot_control.set_context(Offer)


@party_router.callback_query(F.data == "update_english_run")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    await insert_new_words()
    await bot_control.return_to_context()
