import string
from asyncio import gather, create_task, to_thread
from copy import deepcopy
from logging import getLogger
from os import getenv
from random import choice, shuffle
from re import fullmatch, I
from typing import Dict, List

from aiohttp import ClientSession
from tools import DictStorage, Emoji

logger = getLogger()

class WordCard:
    def __init__(
            self,
            word: str,
            data: Dict,
            question: str | list,
            answer: str | list,
            type_: str,
            question_text: str,
            knowledge_scheme: Dict
    ):
        self.word = word
        self.data = data
        self.question = question
        self.answer = answer
        self.type = type_
        self._knowledge_scheme = knowledge_scheme
        self.knowledge_border = len(knowledge_scheme)
        self.question_text = question_text

    @property
    def knowledge_scheme(self):
        return deepcopy(self._knowledge_scheme)


class SuperEnglishDictionary:
    _audio_and_examples_host = "https://api.dictionaryapi.dev"
    _yandex_host = f"https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key={getenv("YANDEX_DICT")}"
    _translate_host = "https://deep-translate1.p.rapidapi.com"
    _translate_headers = {
        "x-rapidapi-key": getenv("RAPID_TRANSLATE"),
        "x-rapidapi-host": "deep-translate1.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    _translations_cache = DictStorage("deep-translate1.p.rapidapi.com")
    _audio_and_examples_cache = DictStorage("api.dictionaryapi.dev")
    _yandex_cache = DictStorage("dictionary.yandex.net")

    @classmethod
    async def extract_cards(cls, word: str, _cache=True) -> List[WordCard] | None:
        if not fullmatch(r"[a-z-]+", word, flags=I):
            logger.error(f"Incorrect word {word} for extract data")
            return

        data = await cls.extract_data(word, _cache)
        try:
            return await cls._build_cards(data, word)
        except (KeyError, Exception) as e_:
            if not _cache:
                logger.critical(f"Impossible extract cards for word {word} after refresh data", exc_info=True)
                e_.add_note(f"Impossible extract cards for word {word} after refresh data")
                raise e_
            logger.error(f"Impossible extract cards for word {word}. Trying refresh data", exc_info=True)
            return await cls.extract_cards(word, _cache=False)

    @staticmethod
    def get_translates(data: Dict):
        return [tr for pos_value in data["pos"].values() for tr in pos_value.get("tr", [])]

    @classmethod
    async def _build_cards(cls, data: Dict, word: str) -> List[WordCard]:
        cards = []
        translates = cls.get_translates(data)
        examples = []
        for pos_value in data["pos"].values():
            exs = pos_value.get("examples")
            if exs:
                examples.extend(exs)

        knowledge_schema = cls.build_knowledge_schema(data)

        if translates:
            cards.append(WordCard(
                word,
                data,
                word,
                translates,
                "default:en-ru",
                f"Give all possible translations, spaces-separated, of the word",
                knowledge_schema
            ))
            shuffle(translates)
            cards.append(WordCard(
                word,
                data,
                translates,
                word,
                "default:ru-en",
                f"What English word can describe each of these words?",
                knowledge_schema
            ))

        if examples:
            example = choice(examples)
            cards.append(WordCard(
                word,
                data,
                example["original"],
                example["translate"],
                "example:en-ru",
                "Translate",
                knowledge_schema
            ))
            cards.append(WordCard(
                word,
                data,
                example["translate"],
                example["original"],
                "example:ru-en",
                "Translate",
                knowledge_schema
            ))
        if not cards:
            logger.warning(f"{Emoji.WARNING} No cards for word {word}")
        return cards

    @classmethod
    def build_knowledge_schema(cls, data: Dict):
        translates = [tr for pos_value in data["pos"].values() for tr in pos_value.get("tr", [])]
        examples = []
        for pos_value in data["pos"].values():
            exs = pos_value.get("examples")
            if exs:
                examples.extend(exs)
        knowledge_schema = {}
        if examples:
            knowledge_schema["example:en-ru"] = {
                "p": 0,
                "g": 0,
                "b": 0
            }
            knowledge_schema["example:ru-en"] = {
                "p": 0,
                "g": 0,
                "b": 0
            }
        if translates:
            knowledge_schema["default:en-ru"] = {
                "p": 0,
                "g": 0,
                "b": 0
            }
            knowledge_schema["default:ru-en"] = {
                "p": 0,
                "g": 0,
                "b": 0
            }
        return knowledge_schema

    @classmethod
    async def extract_data(cls, word: str, cache=True):
        data, audio_and_examples = await gather(cls._yandex(word, cache), cls._audio_and_examples(word, cache))

        logger.debug(f"Word: {word}\n"
                                 f"Audio and examples parsing resume: {audio_and_examples}\n"
                                 f"Yandex parsing resume: {data}")
        if audio_and_examples is not None:
            for pos, examples in audio_and_examples.get("examples", {}).items():
                if examples:
                    try:
                        data["pos"][pos]["examples"] = examples
                    except KeyError:
                        data["pos"][pos] = {}
                        data["pos"][pos]["examples"] = examples
            data["audio"] = audio_and_examples.get("audio")

        logger.debug(f"Resume: {data}")
        return data

    @classmethod
    async def _translate(cls, text: str, cache: bool = True):
        body = {
            "source": "en",
            "target": "ru",
            "q": text
        }

        if cache:
            tr = await cls._translations_cache.get_value_by_key(text)
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
                        await cls._translations_cache.set_value_by_key(text, tr)
                        return tr
                    except KeyError as e:
                        e.add_note(f"Translate API {cls._translate_host} returned unexpected data {data} Status {status}")
                        raise e
                else:
                    logger.error(f"Translate API returned unexpected code {status}")

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
                        logger.critical(f"audio_and_examples API {path} returned unexpected data {data} Status {status}")
                elif status == 404:
                    logger.info(f"No audio_and_examples for word {word}")
                else:
                    logger.error(f"audio_and_examples API returned unexpected code {status}")

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
                try:
                    return await to_thread(cls._yandex_parsing, data)
                except KeyError:
                    return data

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
                    logger.error(f"Yandex dict API returned unexpected code {status}")

    @classmethod
    async def set_yandex_data(cls, word, data):
        await cls._yandex_cache.set_value_by_key(word, data)

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
                "tr": set(),
                "syn": set(),
            }
            for tr in pos.get("tr", set()):
                t = tr.get("text")
                if t and " " not in t and all(True if sym not in string.ascii_letters else False for sym in t):
                    resume["pos"][pos.get("pos", "other")]["tr"].add(t)
                s = tr.get("mean", ())
                if s:
                    for mean in s:
                        resume["pos"][pos.get("pos", "other")]["syn"].add(mean["text"])

        empty_keys = []
        for pos in resume["pos"]:
            if all((not i for i in resume["pos"][pos].values())):
                empty_keys.append(pos)
        for k in empty_keys:
            resume["pos"].pop(k)
        return resume
