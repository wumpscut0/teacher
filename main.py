from asyncio import run
from os import getenv

from admin import GroupTitleScreen
from admin.english import admin_english_router
from admin.shop import admin_shop_router
from user import PrivateTitleScreen, Greetings
from user.english import english_router

from user.shop import private_shop_router
from core.dispatcher import BuildBot
from user.commands import commands_router, BotCommands


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
