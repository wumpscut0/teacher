from aiogram import F
from aiogram.types import CallbackQuery

from core import BotControl, Routers
from core.markups import Info
from models.english import EditEnglish, WordTickCallbackData
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
    markup = await bot_control.current()
    if markup.paginated_buttons[callback_data.index].mark == Emoji.OK:
        markup.paginated_buttons[callback_data.index].mark = Emoji.DENIAL
    else:
        markup.paginated_buttons[callback_data.index].mark = Emoji.OK
    await bot_control.set_current(markup)


@admin_english_router.callback_query(F.data == "merge_words")
async def update_english_run(callback: CallbackQuery, bot_control: BotControl):
    edit_english: EditEnglish = await bot_control.current()
    words = await bot_control.bot_storage.get_value_by_key("words", set())

    if edit_english.action_type == "add":
        for word_button in edit_english.paginated_buttons:
            if word_button.mark == Emoji.OK:
                words.add(word_button.text)
        await bot_control.bot_storage.destroy_key("offer")
    else:
        for word_button in edit_english.paginated_buttons:
            if word_button.mark == Emoji.DENIAL:
                words.remove(word_button.text)

    await bot_control.bot_storage.set_value_by_key("words", words)
    await bot_control.back()


@admin_english_router.callback_query(F.data == "drop_offer")
async def drop_offer(callback: CallbackQuery, bot_control: BotControl):
    await bot_control.bot_storage.destroy_key("offer")
    await bot_control.back()
