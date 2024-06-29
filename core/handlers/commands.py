from aiogram.types import Message

from core import BotControl, Routers
from core import _BotCommands

default_commands_router = Routers.private()
group_commands = Routers.group()


@default_commands_router.message(_BotCommands.start)
async def reset(message: Message, bot_control: BotControl):
    await message.delete()
    user_ids = await bot_control.bot_storage.get_value_by_key("user_ids", set())
    user_id = message.from_user.id
    if user_id not in user_ids:
        await bot_control.greetings()
        user_ids.add(user_id)
        await bot_control.bot_storage.set_value_by_key("user_ids", user_ids)
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
