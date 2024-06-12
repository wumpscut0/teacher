import asyncio

from alt_aiogram import BotControl, BotCommands
from alt_aiogram.dispatcher import dispatcher
from database.queries import create_all


async def main():
    # await create_all()
    await BotControl.bot.set_my_commands(BotCommands.bot_commands)
    await dispatcher.start_polling(BotControl.bot)

if __name__ == "__main__":
    asyncio.run(main())
