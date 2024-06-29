import asyncio
import string
from asyncio import gather, create_task, to_thread
import json
from copy import deepcopy
from os import getenv
from random import choice
from re import fullmatch, I
from typing import Dict, List

from aiohttp import ClientSession
from core.loggers import info_alt_telegram, errors_alt_telegram
from tools import DictStorage


class WordCard:
    def __init__(
            self,
            word: str,
            data: Dict,
            question: str | list,
            answer: str | list,
            type_: str,
            knowledge_scheme: Dict,
            question_text: str
    ):
        self.word = word
        self.data = data
        self.question = question
        self.answer = answer
        self.type = type_
        self._knowledge_scheme = knowledge_scheme
        self.knowledge_border = len(self._knowledge_scheme)
        self.question_text = question_text

    @property
    def knowledge_scheme(self):
        return deepcopy(self._knowledge_scheme)


class WordData:
    def __init__(self, word: str, data: Dict):
        super().__init__()
        self.data = data
        self.word = word

    @property
    def translations(self):
        return [tr for pos_value in self.data["pos"].values() for tr in pos_value.get("tr", [])]

    def create_knowledge(self):
        knowledge = {}
        if self.examples:
            knowledge["example:en-ru"] = {
                "p": 0,
                "g": 0,
                "b": 0
            }
            knowledge["example:ru-en"] = {
                "p": 0,
                "g": 0,
                "b": 0
            }
        if self.translations:
            knowledge["default:en-ru"] = {
                "p": 0,
                "g": 0,
                "b": 0
            }
            knowledge["default:ru-en"] = {
                "p": 0,
                "g": 0,
                "b": 0
            }
        return knowledge

    @property
    def examples(self) -> List[Dict[str, str]]:
        examples_ = []
        for pos_value in self.data["pos"].values():
            examples = pos_value.get("examples")
            if examples:
                examples_.extend(examples)
        return examples_

    @property
    def cards(self):
        cards = []
        knowledge_schema = self.create_knowledge()
        trs = self.translations
        if trs:
            cards.append(WordCard(self.word, self.data, self.word, trs, "default:en-ru", knowledge_schema, f"Give all possible translations, comma-separated, of the word"))
            cards.append(WordCard(self.word, self.data, trs, self.word, "default:ru-en", knowledge_schema, f"What English word can describe each of these words?"))
        ex = self.examples
        if ex:
            ex = choice(ex)
            cards.append(WordCard(self.word, self.data, ex["original"], ex["translate"], "example:en-ru", knowledge_schema, f"Translate"))
            cards.append(WordCard(self.word, self.data, ex["translate"], ex["original"], "example:ru-en", knowledge_schema, f"Translate"))

        return cards

    # def _get_random_example(self):
    #     examples = self.examples
    #     if not examples:
    #         return
    #     example = choice(examples)
    #     if randint(0, 1):
    #         return WordCard(example["original"], example["translate"], "example:en-ru")
    #     return WordCard(example["translate"], example["original"], "example:ru-en")
    #
    # def get_random_side(self) -> WordCard:
    #     if randint(0, 1):
    #         card = self._get_random_example()
    #         if card is None:
    #             return self._get_random_default()
    #         return card
    #     return self._get_random_default()
    #
    # def _get_random_default(self) -> WordCard:
    #     if randint(0, 1):
    #         return WordCard(self.word, self.translations, "default:en-ru")
    #     return WordCard(self.translations, self.word, "default:ru-en")


class SuperEnglishDictionary:
    _audio_and_examples_host = "https://api.dictionaryapi.dev"
    _yandex_host = f"https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key={getenv("YANDEX_DICT")}"
    _translate_host = "https://deep-translate1.p.rapidapi.com"
    _translate_headers = {
        "x-rapidapi-key": getenv("RAPID_TRANSLATE"),
        "x-rapidapi-host": "deep-translate1.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    _word_data_cache = DictStorage("english_words_data")
    _translations_cache = DictStorage("deep-translate1.p.rapidapi.com")
    _audio_and_examples_cache = DictStorage("api.dictionaryapi.dev")
    _yandex_cache = DictStorage("dictionary.yandex.net")

    @classmethod
    async def extract_data(cls, word: str, cache=True) -> WordData | None:
        if not fullmatch(r"[a-z-]+", word, flags=I):
            raise ValueError(f"Incorrect word {word} for extract data")

        if cache:
            data = await cls._word_data_cache.get_value_by_key(word)
            if data:
                return WordData(word, data)

        data, audio_and_examples = await gather(cls._yandex(word), cls._audio_and_examples(word))
        if audio_and_examples is not None:
            for pos, examples in audio_and_examples.get("examples", {}).items():
                if examples:
                    try:
                        data["pos"][pos]["examples"] = examples
                    except KeyError:
                        data["pos"][pos] = {}
                        data["pos"][pos]["examples"] = examples
            data["audio"] = audio_and_examples.get("audio")

        word_data = WordData(word, data)

        if not word_data.translations:
            return None

        cache = await cls._word_data_cache.get()
        cache[word] = data
        await cls._word_data_cache.set(cache)

        return word_data

    @classmethod
    async def _translate(cls, text: str, cache: bool = True):
        body = {
            "source": "en",
            "target": "ru",
            "q": text
        }

        if cache:
            tr = await cls._word_data_cache.get_value_by_key(text)
            if tr:
                return tr

        async with ClientSession(cls._translate_host) as session:
            async with session.post(
                    f"/language/translate/v2",
                    json=body,
                    headers=cls._translate_headers
            ) as response_:
                status = response_.status
                if status == 200:
                    data = await response_.json()
                    try:
                        tr = data["data"]["translations"]["translatedText"]
                        await cls._word_data_cache.set_value_by_key(text, tr)
                        return tr
                    except KeyError as e:
                        e.add_note(f"Translate API {cls._translate_host} returned unexpected data {data} Status {status}")
                        raise e
                else:
                    errors_alt_telegram.error(f"Translate API returned unexpected code {status}")

    @classmethod
    async def _audio_and_examples(cls, word: str, cache: bool = True):
        if cache:
            data = await cls._audio_and_examples_cache.get_value_by_key(word)
            if data:
                return await cls._audio_and_examples_parsing(data, word)

        path = f"{cls._audio_and_examples_host}/api/v2/entries/en/{word}"
        async with ClientSession() as session:
            async with session.get(path) as response_:
                status = response_.status
                if status == 200:
                    data = await response_.json()
                    try:
                        await cls._audio_and_examples_cache.set_value_by_key(word, data)
                        return await cls._audio_and_examples_parsing(data, word)
                    except KeyError:
                        info_alt_telegram.critical(f"audio_and_examples API {path} returned unexpected data {data} Status {status}")
                elif status == 404:
                    info_alt_telegram.warning(f"No audio_and_examples for word {word}")
                else:
                    errors_alt_telegram.error(f"audio_and_examples API returned unexpected code {status}")

    @classmethod
    async def _audio_and_examples_parsing(cls, data: Dict, word: str):
        resume = {
            "audio": [],
            "examples": {}
        }
        for entry in data:
            for phonetic in entry["phonetics"]:
                audio = phonetic.get("audio")
                if audio:
                    resume["audio"].append(audio)

            for meaning in entry["meanings"]:
                pos_name = meaning["partOfSpeech"]
                if resume["examples"].get(pos_name) is None:
                    resume["examples"][pos_name] = []
                tasks = []
                for definition in meaning["definitions"]:
                    example = definition.get("example")
                    if example and word in example:
                        tasks.append(create_task(cls._translate(example)))
                        ex = {
                            "original": example,
                        }
                        resume["examples"][pos_name].append(ex)
                for i, tr in enumerate(await gather(*tasks)):
                    resume["examples"][pos_name][i]["translate"] = tr
        return resume

    @classmethod
    async def _yandex(cls, word: str, cache: bool = True):
        if cache:
            data = await cls._yandex_cache.get_value_by_key(word)
            if data:
                return await to_thread(cls._yandex_parsing, data)

        if not fullmatch(r"[a-z-]+", word, flags=I):
            raise ValueError(f"Incorrect text {word} to yandex translate")

        async with ClientSession() as session:
            async with session.get(
                    f"{cls._yandex_host}&lang=en-ru&text={word}",
            ) as response_:
                status = response_.status
                if status == 200:
                    data = await response_.json()
                    try:
                        await cls._yandex_cache.set_value_by_key(word, data)
                        return await to_thread(cls._yandex_parsing, data)
                    except KeyError as e_:
                        e_.add_note(
                            f"Yandex dict API {cls._yandex_host} returned unexpected data {data} Status {status}"
                        )
                        raise e_
                else:
                    errors_alt_telegram.error(f"Yandex dict API returned unexpected code {status}")

    @classmethod
    def _yandex_parsing(cls, data: Dict):
        resume = {
            "pos": {
            }
        }
        for pos in data["def"]:
            ts = pos.get("ts")
            if ts:
                resume["ts"] = ts
            resume["pos"][pos.get("pos", "other")] = {
                "tr": [],
                "syn": [],
            }
            for tr in pos.get("tr", []):
                t = tr.get("text")
                if t and all(True if sym not in string.ascii_letters else False for sym in t):
                    resume["pos"][pos.get("pos", "other")]["tr"].append(t)
                s = tr.get("mean", ())
                if s:
                    resume["pos"][pos.get("pos", "other")]["syn"].extend((mean["text"] for mean in s))
        empty_keys = []
        for pos in resume["pos"]:
            if all((not i for i in resume["pos"][pos].values())):
                empty_keys.append(pos)
        for k in empty_keys:
            resume["pos"].pop(k)
        return resume


if __name__ == "__main__":
    w = "introduce"
    e = asyncio.run(SuperEnglishDictionary.extract_data(w, cache=False))
    with open(f"{w}.json", "w", encoding="utf-8") as file:
        json.dump(e.data, file, indent=4, ensure_ascii=False)
