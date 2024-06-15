import asyncio
import os

from cache import Cache
from database.queries import drop_all, create_all
from group_markups import GroupPartyTitleScreen
from private_markups import PrivateTuurngaidTitleScreen, Greetings
from core.dispatcher import BuildBot
from group_handlers import party_router
from private_handlers import english_router
from private_handlers.commands import commands_router, BotCommands


async def main():
    # await drop_all()
    # await create_all()
    await BuildBot(
        commands_router,
        english_router,
        party_router,
        token=os.getenv("TOKEN"),
        private_title_screen=PrivateTuurngaidTitleScreen,
        group_title_screen=GroupPartyTitleScreen,
        hello_screen=Greetings,
        cache=Cache
    ).start_polling(BotCommands.commands())


if __name__ == "__main__":
    asyncio.run(main())
