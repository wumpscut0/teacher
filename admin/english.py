from aiogram import F
from aiogram.types import CallbackQuery

from api import SuperEnglishDictionary
from core import BotControl, Routers
from core.markups import Info
from models.english import EditEnglish, WordTickCallbackData, EditWordCallbackData, ResetWordCallbackData
from models.word import Word, TranslateTickCallbackData
from tools import Emoji

admin_english_router = Routers.group()


@admin_english_router.callback_query(F.data == "add_words")
async def get_english(callback: CallbackQuery, bot_control: BotControl):
    offer = await bot_control.bot_storage.get_value_by_key("offer", set())

    if not offer:
        await bot_control.append(Info(f"No offers so far {Emoji.WEB}"))
        return

    await bot_control.append(EditEnglish("add", offer))


@admin_english_router.callback_query(F.data == "edit_words")
async def edit_english_run(callback: CallbackQuery, bot_control: BotControl):
    words = await bot_control.bot_storage.get_value_by_key("words", set())

    if not words:
        await bot_control.append(Info(f"No words so far {Emoji.WEB}"))
        return

    await bot_control.append(EditEnglish("edit", words))


@admin_english_router.callback_query(WordTickCallbackData.filter())
async def marking_words(callback: CallbackQuery, callback_data: WordTickCallbackData, bot_control: BotControl):
    edit_english: EditEnglish = await bot_control.get_current()
    edit_english.marking_words(callback_data.index)
    await bot_control.set_current(edit_english)


@admin_english_router.callback_query(EditWordCallbackData.filter())
async def edit_word(callback: CallbackQuery, callback_data: EditWordCallbackData, bot_control: BotControl):
    await bot_control.append(Word(callback_data.word, await SuperEnglishDictionary.extract_data(callback_data.word)))


@admin_english_router.callback_query(ResetWordCallbackData.filter())
async def reset_word(callback: CallbackQuery, callback_data: ResetWordCallbackData, bot_control: BotControl):
    edit_english: EditEnglish = await bot_control.get_current()
    await edit_english.reset_word(callback_data.word)
    await bot_control.append(Info(f"Reset completed {Emoji.MAGIC_SPHERE}"))


@admin_english_router.callback_query(TranslateTickCallbackData.filter())
async def marking_ru_default(callback: CallbackQuery, callback_data: TranslateTickCallbackData, bot_control: BotControl):
    word: Word = await bot_control.get_current()
    word.tick_translate(callback_data.index)
    await bot_control.set_current(word)


@admin_english_router.callback_query(F.data == "merge_ru_default")
async def update_word_ru_default(callback: CallbackQuery, bot_control: BotControl):
    word: Word = await bot_control.get_current()
    await word.merge_ru_default()
    await bot_control.back()


@admin_english_router.callback_query(F.data == "merge_words")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    edit_english: EditEnglish = await bot_control.get_current()
    await edit_english.merge_words(bot_control)
    await bot_control.back()


@admin_english_router.callback_query(F.data == "drop_offer")
async def drop_offer(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.bot_storage.destroy_key("offer")
    await bot_control.back()
