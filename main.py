import asyncio
import os

from core import BotControl, WindowBuilder
from core.markups import TextWidget
from group import GroupTitleScreen
from group.english import admin_english_router
from group.shop import admin_shop_router
from private import PrivateTitleScreen, Greetings
from private.english import english_router

from private.shop import private_shop_router

from core.dispatcher import BuildBot


from private.commands import commands_router, BotCommands
from tools import Emoji


class CustomBotControl(BotControl):
    async def get_private_title_screen(self) -> WindowBuilder:
        window_builder = await super().get_private_title_screen()
        window_builder.add_texts_rows(
            TextWidget(text=f"{Emoji.DNA} {await self.user_storage.get_value_by_key("english:total_dna", 0)}"
                            f"  {Emoji.CUBE} {await self.user_storage.get_value_by_key("english:keys", 0)}"),

        )
        return window_builder


async def main():
    await BuildBot(
        commands_router,
        english_router,
        admin_english_router,
        admin_shop_router,
        private_shop_router,
        token=os.getenv("TOKEN"),
        private_title_screen=PrivateTitleScreen(),
        group_title_screen=GroupTitleScreen(),
        hello_screen=Greetings(),
        bot_control_schema=CustomBotControl
    ).start_polling(BotCommands.commands())


if __name__ == "__main__":
    asyncio.run(main())
