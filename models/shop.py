from typing import Literal, Dict

from aiogram.filters.callback_data import CallbackData

from FSM import States
from api import SuperEnglishDictionary
from core import WindowBuilder, BotControl
from core.markups import ButtonWidget, TextWidget, Info
from models.english import knowledge_as_progress_string
from tools import Emoji


class BuyingContentCallbackData(CallbackData, prefix="buying_content"):
    name: str


class EditContentCallbackData(CallbackData, prefix="edit_content"):
    name: str


class Shop(WindowBuilder):
    _actions = {
        "buy": BuyingContentCallbackData,
        "edit": EditContentCallbackData
    }

    def __init__(self, action_type: Literal["buy", "edit"]):
        self.temp_balance = None
        self.action_type = action_type
        super().__init__()
        if action_type == "edit":
            self.frozen_text.add_texts_rows(TextWidget(text=f"Edit shop {Emoji.TAG}"))

    async def __call__(self, bot_control: BotControl):
        shop = await bot_control.bot_storage.get_value_by_key("shop", {})
        if not shop:
            await bot_control.append(Info(f"Nothing to show {Emoji.BAN}"))
            self.initializing = False
            return

        if self.action_type == "buy":
            collection = await bot_control.user_storage.get_value_by_key("collection", {})
            shop = {k: v for k, v in shop.items() if k not in collection}

        if not shop:
            await bot_control.pop_last()
            await bot_control.append(Info(f"Empty {Emoji.WEB}"))
            self.initializing = False
            return

        buttons = []
        for name, content in shop.items():
            button_text = name + " "
            for currency, cost in content["cost"].items():
                if int(cost) > 0:
                    button_text += f"{currency} {cost} "
            buttons.append(ButtonWidget(
                text=button_text,
                callback_data=self._actions[self.action_type](name=name))
            )
        self.paginated_buttons = buttons

        if self.action_type == "buy":
            await self.balance_display(bot_control)

    async def balance_display(self, bot_control: BotControl):
        dna = await bot_control.user_storage.get_value_by_key("english:total_dna", 0)
        cube = await bot_control.user_storage.get_value_by_key("english:keys", 0)
        star = 0

        user_knowledge = await bot_control.user_storage.get_value_by_key("english:knowledge", {})
        for word in await bot_control.bot_storage.get_value_by_key("words", set()):
            data = await SuperEnglishDictionary.extract_data(word)
            if data["pos"]:
                knowledge_size = len(SuperEnglishDictionary.build_knowledge_schema(data))
                star += knowledge_as_progress_string(user_knowledge.get(word, {}), knowledge_size).count(Emoji.STAR)

        self.temp_balance = {
            Emoji.DNA: dna,
            Emoji.CUBE: cube,
            Emoji.STAR: star
        }
        self.add_texts_rows(TextWidget(text=f"{Emoji.DNA} {dna} {Emoji.CUBE} {cube} {Emoji.STAR} {star}"))

    async def buying(self, bot_control: BotControl, name: str):
        shop_data = await bot_control.bot_storage.get_value_by_key("shop")
        item = shop_data[name]

        dna = self.temp_balance[Emoji.DNA]
        cube = self.temp_balance[Emoji.CUBE]
        dna -= int(item["cost"][Emoji.DNA])
        cube -= int(item["cost"][Emoji.CUBE])
        await bot_control.user_storage.set_value_by_key("english:total_dna", dna)
        await bot_control.user_storage.set_value_by_key("english:keys", cube)
        collection = await bot_control.user_storage.get_value_by_key("collection", {})
        collection[name] = item
        await bot_control.user_storage.set_value_by_key("collection", collection)


class Content(WindowBuilder):
    def __init__(
            self,
            action_type: Literal["add", "edit"],
            *,
            content_type: Literal["photo", "audio"] | None = None,
            content: str | None = None,
            temp_name: str = Emoji.RED_QUESTION,
            temp_dna_cost: int = 0,
            temp_cube_cost: int = 0,
            temp_star_cost: int = 0,
    ):
        super().__init__(
            state=States.input_photo_audio_content,
            back_text=f"{Emoji.DENIAL} Cancel",
            back_callback_data="update"
        )
        if content_type is not None:
            self.type = content_type
        if content_type == "photo":
            self.photo = content
        else:
            self.voice = content
        self.action_type = action_type
        self.temp_name = temp_name
        self.temp_old_name = temp_name
        self.temp_dna_cost = temp_dna_cost
        self.temp_cube_cost = temp_cube_cost
        self.temp_star_cost = temp_star_cost

    def __call__(self, bot_control: BotControl):
        self.state = None
        self.add_texts_rows(TextWidget(text=f"{Emoji.PENCIL} {self.temp_name}\n"
                                            f"{Emoji.DNA} {self.temp_dna_cost} "
                                            f"{Emoji.CUBE} {self.temp_cube_cost} "
                                            f"{Emoji.STAR} {self.temp_star_cost} "))
        self.add_buttons_as_new_row(ButtonWidget(text=Emoji.COLORS, callback_data="edit_content"))
        self.add_buttons_as_new_row(
            ButtonWidget(text=Emoji.PENCIL, callback_data="edit_name"),
            ButtonWidget(text=Emoji.DNA, callback_data="edit_dna_cost"),
            ButtonWidget(text=Emoji.CUBE, callback_data="edit_cube_cost"),
            ButtonWidget(text=Emoji.STAR, callback_data="edit_star_cost"),
        )
        if self.action_type == "edit":
            self.add_buttons_as_new_row(ButtonWidget(
                text=f"Delete {self.temp_name} {Emoji.DENIAL}",
                callback_data="delete_content"
            ))
        self.add_buttons_as_new_row(ButtonWidget(text=f"Save {Emoji.FLOPPY_DISC}", callback_data="merge_content"))

    def input_content_display(self):
        self.state = States.input_photo_audio_content
        self.add_texts_rows(TextWidget(text=f"Send a content {Emoji.SHOP}\nPhoto {Emoji.PHOTO} or audio {Emoji.AUDIO}"))

    def input_name_display(self):
        self.state = States.input_text_content_name
        self.add_texts_rows(TextWidget(text=f"Enter a content name {Emoji.PENCIL}\nMax length is 20"))

    def input_dna_cost_display(self):
        self.state = States.input_integer_dna_cost
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.DNA} as integer"))

    def input_cube_cost_display(self):
        self.state = States.input_integer_cube_cost
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.CUBE} as integer"))

    def input_star_cost_display(self):
        self.state = States.input_integer_star_cost
        self.add_texts_rows(TextWidget(text=f"Enter {Emoji.STAR} as integer"))

    async def delete(self, bot_control):
        assert self.action_type == "edit"

        shop: Dict = await bot_control.bot_storage.get_value_by_key("shop")
        item = shop.pop(self.temp_old_name)
        await bot_control.bot_storage.set_value_by_key("shop", shop)
        await bot_control.set_current(Info(
                f"Item {self.temp_old_name} {Emoji.PHOTO if item["type"] == "photo" else Emoji.AUDIO}"
                f" deleted {Emoji.CANDLE}", back_callback_data="update"
        ))

    async def merge_content(self, bot_control):
        if not self.temp_name or self.temp_name == Emoji.RED_QUESTION:
            await bot_control.append(Info("Name required"))
            self.initializing = False
            return

        if self.type == "text":
            await bot_control.append(Info("Content required"))
            self.initializing = False
            return

        shop = await bot_control.bot_storage.get_value_by_key("shop", {})

        if self.action_type == "add" and self.temp_name in shop:
            await bot_control.append(Info(f"Name {self.temp_name} already exist"))
            self.initializing = False
            return

        if self.action_type == "edit":
            shop.pop(self.temp_old_name)

        shop[self.temp_name] = {
            "type": self.type,
            "content": self.photo if self.type == "photo" else self.voice,
            "cost": {
                Emoji.DNA: int(self.temp_dna_cost),
                Emoji.CUBE: int(self.temp_cube_cost),
                Emoji.STAR: int(self.temp_star_cost)
            }
        }
        await bot_control.bot_storage.set_value_by_key("shop", shop)
