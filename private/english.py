from asyncio import gather
from random import shuffle

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from api import SuperEnglishDictionary
from core.markups import Info, Conform

from core import BotControl, Routers
from models.english import English, InspectEnglishRun, BanWordCallbackData
from tools import Emoji

english_router = Routers.private()


@english_router.callback_query(F.data == "run_english")
async def run_english(callback: CallbackQuery, bot_control: BotControl):
    words = await bot_control.bot_storage.get_value_by_key("words")

    if not words:
        await bot_control.append(
            Info(f"No words so far {Emoji.CRYING_CAT}\nYou can suggest a word to Tuurngaid /offer_word")
        )
        return

    ban_list = await bot_control.user_storage.get_value_by_key("english:ban_list", set())
    deck = []
    for cards in (await gather(*(SuperEnglishDictionary.extract_cards(word) for word in words if word not in ban_list))):
        deck.extend(cards)

    if not deck:
        await bot_control.append(
            Info(f"All words banned {Emoji.CRYING_CAT}")
        )
        return

    shuffle(deck)

    english = English(deck)
    await bot_control.append(
        english
    )


@english_router.message(States.input_text_word_translate, F.text)
async def accept_input_text_word_translate(message: Message, bot_control: BotControl):
    answer = message.text
    await message.delete()

    if len(answer) > 200:
        await bot_control.append(Info(f"Max symbols is {200} {Emoji.CRYING_CAT}"))
        return

    english: English = await bot_control.get_current()
    await english.process_answer(answer, bot_control)
    await bot_control.set_current(english)


@english_router.callback_query(F.data == "reference")
async def reference(callback: CallbackQuery, bot_control: BotControl):
    english: English = await bot_control.get_current()
    english.reference()
    await bot_control.append(english)


@english_router.callback_query(F.data == "draw_card")
async def draw_card(callback: CallbackQuery, bot_control: BotControl):
    english: English = await bot_control.get_current()
    try:
        english.draw_card()
    except IndexError:
        english.result()

    await bot_control.set_current(english)


@english_router.callback_query(F.data == "request_to_flush_run")
async def result_english_run(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.append(Conform(f"Do you really want to flush current run?\n"
                                     f"(All data will be save {Emoji.FLOPPY_DISC})",
                                     yes_callback_data="flush_run",
                                     yes_text=f"Yes {Emoji.WAVE}", no_text=f"Continue {Emoji.RIGHT}"))


@english_router.callback_query(F.data == "flush_run")
async def result_english_run(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.pop_last()
    english: English = await bot_control.get_current()
    english.result()
    await bot_control.set_current(english)


@english_router.callback_query(F.data == "inspect_english_run")
async def inspect_english_run(callback: CallbackQuery, bot_control: BotControl):
    words = await bot_control.bot_storage.get_value_by_key("words")
    if not words:
        await bot_control.append(
            Info(f"No words so far {Emoji.CRYING_CAT}\n"
                 f"You can suggest a word to Tuurngaid /offer_word")
        )
        return

    await bot_control.append(InspectEnglishRun())


@english_router.callback_query(BanWordCallbackData.filter())
async def baning_words(callback: CallbackQuery, callback_data: BanWordCallbackData, bot_control: BotControl):
    inspect: InspectEnglishRun = await bot_control.get_current()
    await inspect.banning(bot_control, callback_data.index, callback_data.word)
    await bot_control.set_current(inspect)


@english_router.callback_query(F.data == "ban_all")
async def ban_all(callback: CallbackQuery, bot_control: BotControl):
    inspect: InspectEnglishRun = await bot_control.get_current()
    await inspect.ban_all(bot_control)
    await bot_control.set_current(inspect)


@english_router.callback_query(F.data == "unban_all")
async def unban_all(callback: CallbackQuery, bot_control: BotControl):
    inspect: InspectEnglishRun = await bot_control.get_current()
    await inspect.unban_all(bot_control)
    await bot_control.set_current(inspect)
