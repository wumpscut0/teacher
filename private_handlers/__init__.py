from asyncio import gather
from random import shuffle

from aiogram import F
from aiogram.types import CallbackQuery, Message

from FSM import States
from api import SuperEnglishDictionary
from core.markups import Info, Conform

from core import BotControl, Routers
from private_markups import English, InspectEnglishRun, BanWordCallbackData
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
    knowledge = await bot_control.user_storage.get_value_by_key("english:knowledge", {})

    english = English(deck, knowledge)
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

    english: English = await bot_control.current()
    english.process_answer(answer)
    await bot_control.user_storage.set_value_by_key("english:knowledge", english.knowledge)
    updated_total_dna = await bot_control.user_storage.get_value_by_key("english:total_dna", 0) + english.temp_dna
    await bot_control.user_storage.set_value_by_key("english:total_dna", updated_total_dna)
    new_keys = await bot_control.user_storage.get_value_by_key("english:keys", 0) + english.temp_keys
    await bot_control.user_storage.set_value_by_key("english:keys", new_keys)
    await bot_control.set_current(english)


@english_router.callback_query(F.data == "reference")
async def reference(callback: CallbackQuery, bot_control: BotControl):
    english: English = await bot_control.current()
    english.reference()
    await bot_control.append(english)


@english_router.callback_query(F.data == "draw_card")
async def draw_card(callback: CallbackQuery, bot_control: BotControl):
    english: English = await bot_control.current()
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
                                     yes_text=f"Yes {Emoji.WAVE}", no_text=f"Continue {Emoji.RIGHT}"
                                     ))


@english_router.callback_query(F.data == "flush_run")
async def result_english_run(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.pop_last()
    english: English = await bot_control.current()
    english.result()
    await bot_control.set_current(english)


@english_router.callback_query(F.data == "inspect_english_run")
async def result_english_run(callback: CallbackQuery, bot_control: BotControl):
    words = await bot_control.bot_storage.get_value_by_key("words")
    if not words:
        await bot_control.append(
            Info(f"No words so far {Emoji.CRYING_CAT}\nYou can suggest a word to Tuurngaid /offer_word")
        )
        return
    words_ = []
    for word in words:
        data = await SuperEnglishDictionary.extract_data(word)
        knowledge_size = len(SuperEnglishDictionary.build_knowledge_schema(data))
        words_.append((word, knowledge_size))

    knowledge = await bot_control.user_storage.get_value_by_key("english:knowledge", {})
    ban_list = await bot_control.user_storage.get_value_by_key("english:ban_list", set())
    await bot_control.append(InspectEnglishRun(words_, ban_list, knowledge))


@english_router.callback_query(BanWordCallbackData.filter())
async def baning_words(callback: CallbackQuery, callback_data: BanWordCallbackData, bot_control: BotControl):
    markup = await bot_control.current()
    ban_list = await bot_control.user_storage.get_value_by_key("english:ban_list", set())
    if markup.data[callback_data.index].mark == Emoji.OK:
        markup.data[callback_data.index].mark = Emoji.DENIAL
        ban_list.add(callback_data.word)
    else:
        markup.data[callback_data.index].mark = Emoji.OK
        ban_list.remove(callback_data.word)
    await bot_control.user_storage.set_value_by_key("english:ban_list", ban_list)
    await bot_control.set_current(markup)


@english_router.callback_query(F.data == "ban_all")
async def ban_all(callback: CallbackQuery, bot_control: BotControl):
    markup = await bot_control.current()
    words = await bot_control.bot_storage.get_value_by_key("words")
    await bot_control.user_storage.set_value_by_key("english:ban_list", set(words))
    for button in markup.data:
        button.mark = Emoji.DENIAL
    await bot_control.set_current(markup)


@english_router.callback_query(F.data == "unban_all")
async def unban_all(callback: CallbackQuery, bot_control: BotControl):
    markup = await bot_control.current()
    await bot_control.user_storage.destroy_key("english:ban_list")
    for button in markup.data:
        button.mark = Emoji.OK
    await bot_control.set_current(markup)
