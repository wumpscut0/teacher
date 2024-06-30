import asyncio
import os

from core import BotControl, WindowBuilder
from core.markups import TextWidget, DataTextWidget
from group_markups import GroupPartyTitleScreen
from private_markups import PrivateTuurngaidTitleScreen, Greetings
from core.dispatcher import BuildBot
from group_handlers import party_router
from private_handlers import english_router
from private_handlers.commands import commands_router, BotCommands
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
        party_router,
        token=os.getenv("TOKEN"),
        private_title_screen=PrivateTuurngaidTitleScreen(),
        group_title_screen=GroupPartyTitleScreen(),
        hello_screen=Greetings(),
        bot_control_schema=CustomBotControl
    ).start_polling(BotCommands.commands())


if __name__ == "__main__":
    asyncio.run(main())
