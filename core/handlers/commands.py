from aiogram.types import Message

from core import BotControl, Routers
from core.dispatcher import BotCommands

from database.queries import insert_user

default_commands_router = Routers.private()

# TODO detach database


@default_commands_router.message(BotCommands.start)
async def continue_(message: Message, bot_control: BotControl):
    await message.delete()
    if await insert_user(bot_control.chat_id):
        await bot_control.dig(
            bot_control.title_screens.private_title_screen,
            bot_control.title_screens.greetings
        )
        return
    await bot_control.look_around()


@default_commands_router.message(BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.sleep()
