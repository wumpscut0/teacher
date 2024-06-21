from asyncio import gather, create_task
import json
from os import getenv
from random import randint, choice
from re import fullmatch, I
from typing import Dict, List

from aiohttp import ClientSession
from cache import WordDataCache
from core.loggers import info, errors


class WordData:
    def __init__(self, word: str, data: Dict):
        super().__init__()
        self.data = data
        self.word = word

    @property
    def _translations(self):
        return [tr for pos_value in self.data["pos"].values() for tr in pos_value["tr"]]

    @property
    def _examples(self) -> List[Dict[str, str]]:
        examples_ = []
        for pos_value in self.data["pos"].values():
            examples = pos_value.get("examples")
            if examples:
                examples_.extend(examples)
        return examples_

    def get_random_example(self):
        example = choice(self._examples)
        if randint(0, 1):
            return {
                "original": example["original"],
                "translate": example["translate"]
            }
        return {
            "original": example["translate"],
            "translate": example["original"]
        }

    def get_random_default(self):
        if randint(0, 1):
            return {
                "original": self.word,
                "translate": self._translations
            }
        return {
            "original": self._translations,
            "translate": self.word
        }


class SuperEnglishDictionary:
    _audio_and_examples_host = "https://api.dictionaryapi.dev"
    _yandex_host = f"https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key={getenv("YANDEX_DICT")}"
    _translate_host = "https://deep-translate1.p.rapidapi.com"
    _translate_headers = {
        "x-rapidapi-key": getenv("RAPID_TRANSLATE"),
        "x-rapidapi-host": "deep-translate1.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    _word_data_cache = WordDataCache()

    @classmethod
    async def extract_data(cls, word: str) -> WordData:
        if not fullmatch(r"[a-z-]+", word, flags=I):
            raise ValueError(f"Incorrect word {word} for extract data")

        data = cls._word_data_cache[word]
        if data is not None:
            return data

        data, audio_and_examples = await gather(cls._yandex(word), cls._audio_and_examples(word))
        for pos, examples in audio_and_examples["examples"].items():
            data["pos"][pos]["examples"] = examples
        data["audio"] = audio_and_examples["audio"]

        cls._word_data_cache[word] = data
        return WordData(word, data)

    @classmethod
    async def _translate(cls, text: str):
        if not fullmatch(r"""[a-z-,?.!:";' ]+""", text, flags=I):
            raise ValueError(f"Incorrect text {text} to translate")

        body = {
            "source": "en",
            "target": "ru",
            "q": text
        }

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
                        return data["data"]["translations"]["translatedText"]
                    except KeyError:
                        raise KeyError(f"Translate API {cls._translate_host} returned unexpected data {data}\n"
                                       f"Status {status}")
                else:
                    errors.error(f"Translate API returned unexpected code {status}")

    @classmethod
    async def _audio_and_examples(cls, word: str):
        path = f"{cls._audio_and_examples_host}/api/v2/entries/en/{word}"
        async with ClientSession() as session:
            async with session.get(path) as response_:
                status = response_.status
                if status == 200:
                    data = await response_.json()
                    try:
                        return await cls._audio_and_examples_parsing(data, word)
                    except KeyError:
                        info.critical(f"audio_and_examples API {path} returned unexpected data {data} Status {status}")
                elif status == 404:
                    info.warning(f"No audio_and_examples for word {word}")
                else:
                    errors.error(f"audio_and_examples API returned unexpected code {status}")

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
    async def _yandex(cls, word: str):
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
                        return cls._yandex_parsing(data)
                    except KeyError:
                        raise KeyError(
                            f"Yandex dict API {cls._yandex_host} returned unexpected data {data} Status {status}"
                        )
                else:
                    errors.error(f"Yandex dict API returned unexpected code {status}")

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
            resume["pos"][pos["pos"]] = {
                "tr": [],
                "syn": [],
            }
            for tr in pos["tr"]:
                resume["pos"][pos["pos"]]["tr"].append(tr["text"])
                resume["pos"][pos["pos"]]["syn"].extend((mean["text"] for mean in tr.get("mean", ())))
        return resume


# w = "span"
# e = asyncio.run(SuperEnglishDictionary.extract_data(w))
# with open("e.json", "w", encoding="utf-8") as file:
#     json.dump(e, file, indent=4, ensure_ascii=False)
