from aiogram.types import Message

from core import BotControl, Routers
from core.dispatcher import BotCommands

default_commands_router = Routers.private()


@default_commands_router.message(BotCommands.start)
async def continue_(message: Message, bot_control: BotControl):
    await message.delete()
    if bot_control.user_id not in bot_control.title_screens.users_ids:
        await bot_control.dig(
            bot_control.title_screens.private_title_screen,
            bot_control.title_screens.greetings
        )
        bot_control.title_screens.add_user_id(bot_control.user_id)
        return
    await bot_control.look_around()


@default_commands_router.message(BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.sleep()
