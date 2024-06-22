from aiogram.filters import Command
from aiogram.types import BotCommand

from tools import Emoji, ImmuneList, ImmuneSet, ImmuneDict


class _SetUpWindows(ImmuneDict):
    def __init__(self, bot_id: str | int):
        super().__init__(f"{bot_id}:set_up_windows")


class _UsersIds(ImmuneSet):
    def __init__(self, bot_id: str | int):
        super().__init__(f"{bot_id}:user_ids")


class _MessagesIds(ImmuneList):
    def __init__(self, chat_id: str | int, bot_id: str | int):
        super().__init__(f"{chat_id}:{bot_id}:messages_ids")


class _BotCommands:
    start = Command("start")
    exit = Command("exit")
    continue_ = Command("continue")

    @classmethod
    def commands(cls):
        return [
            BotCommand(
                command=f"/continue", description=f"Continue {Emoji.ZAP}"
            ),
            BotCommand(
                command="/exit", description=f"Close {Emoji.ZZZ}"
            ),
            BotCommand(
                command="/start", description=f"Reboot {Emoji.CYCLE}"
            )
        ]
