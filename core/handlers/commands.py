import os.path

from aiogram.types import Message, FSInputFile

from core import BotControl, Routers
from core.dispatcher import BotCommands
from core.markups.photo_messages import Photo

from database.queries import insert_user

default_commands_router = Routers.private()
CONTENT_LENGTH = 100


@default_commands_router.message(BotCommands.start)
async def start(message: Message, bot_control: BotControl, hello):
    await message.delete()
    if await insert_user(bot_control.chat_id):
        print(hello.text_map)
        await bot_control.update_photo_message(hello)
        return
    await bot_control.return_to_context()


@default_commands_router.message(BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.delete_message(bot_control._messages_pool.last_message_id_from_the_chat)
