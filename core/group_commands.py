from aiogram.types import Message

from core import Routers, BotCommands, BotControl

group_commands = Routers.group()


@group_commands.message(BotCommands.start)
async def start(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.look_around()


@group_commands.message(BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.sleep()
