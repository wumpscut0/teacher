from aiogram.types import Message

from core import BotControl, Routers
from core.objects import _BotCommands

default_commands_router = Routers.private()
group_commands = Routers.group()


@default_commands_router.message(_BotCommands.start)
async def reset(message: Message, bot_control: BotControl):
    await message.delete()
    if bot_control.user_id not in bot_control.user_uds:
        await bot_control.greetings()
        bot_control.user_uds.add(bot_control.user_id)
        return
    await bot_control.reset()


@default_commands_router.message(_BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.clear_chat(force=True)


@default_commands_router.message(_BotCommands.continue_)
async def continue_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.push()


@group_commands.message(_BotCommands.start)
async def reset(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.reset()


@group_commands.message(_BotCommands.exit)
async def exit_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.clear_chat(force=True)


@group_commands.message(_BotCommands.continue_)
async def continue_(message: Message, bot_control: BotControl):
    await message.delete()
    await bot_control.push()
