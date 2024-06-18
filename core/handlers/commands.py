from aiogram.types import Message

from core import BotControl, Routers
from core.dispatcher import BotCommands

default_commands_router = Routers.private()


@default_commands_router.message(BotCommands.start)
async def reset(message: Message, bot_control: BotControl):
    await message.delete()
    if bot_control.user_id not in bot_control.title_screens.users_ids:
        await bot_control.dig(
            await bot_control.title_screens.greetings.update()
        )
        bot_control.title_screens.add_user_id(bot_control.user_id)
        return
    await bot_control.reset()


@default_commands_router.message(BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.sleep()


@default_commands_router.message(BotCommands.continue_)
async def continue_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.look_around()
