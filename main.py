from asyncio import run
from os import getenv

from group import GroupTitleScreen
from group.english import admin_english_router
from group.shop import admin_shop_router
from private import PrivateTitleScreen, Greetings
from private.english import english_router

from private.shop import private_shop_router
from core.dispatcher import BuildBot
from private.commands import commands_router, BotCommands


async def main():
    await BuildBot(
        commands_router,
        english_router,
        admin_english_router,
        admin_shop_router,
        private_shop_router,
        token=getenv("TOKEN"),
        private_title_screen=PrivateTitleScreen(),
        group_title_screen=GroupTitleScreen(),
        greetings=Greetings(),
    ).start_polling(BotCommands.commands())


if __name__ == "__main__":
    run(main())
