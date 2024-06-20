import asyncio
import json
import os
import re
from typing import List, Dict

from aiohttp import ClientSession
from cache import TranslateCache, WordEntriesCache, YandexDictCache, WordDataCache
from core.loggers import info, errors


class SuperEnglishDictionary:
    _entries_host = "https://api.dictionaryapi.dev"

    _translate_host = "https://deep-translate1.p.rapidapi.com"
    _translate_headers = {
        "x-rapidapi-key": os.getenv("RAPID_TRANSLATE"),
        "x-rapidapi-host": "deep-translate1.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    _translate_cache = TranslateCache()

    _yandex_host = f"https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key={os.getenv("YANDEX_DICT")}"
    _word_data_cache = WordDataCache()

    @classmethod
    async def extract_data(cls, word: str):


        data = cls._word_data_cache[word]
        if data is not None:
            return data

    @classmethod
    async def _audio_and_examples(cls, word: str):
        if not re.fullmatch(r"[a-zA-Z-]+", word):
            raise ValueError(f"Incorrect word {word} for audio_and_examples")



        path = f"{cls._entries_host}/api/v2/entries/en/{word}"
        async with ClientSession() as session:
            async with session.get(path) as response_:
                status = response_.status
                if status == 200:
                    data = await response_.json()
                    try:
                        data = cls._audio_and_examples_parsing(data)
                    except KeyError:
                        info.critical(f"audio_and_examples API {path} returned unexpected data {data} Status {status}")
                        return
                elif status == 404:
                    info.warning(f"No audio_and_examples for word {word}")
                    return
                else:
                    errors.error(f"audio_and_examples API returned unexpected code {status}")
                    return

                cls._entries_cache[word] = data
                return data

    @classmethod
    def _audio_and_examples_parsing(cls, entries: List):
        word = {
            "audios": [],
        }
        for entry in entries:
            for phonetic in entry["phonetics"]:
                audio = phonetic.get("audio")
                if audio:
                    word["audios"].append(audio)

            for meaning in entry["meanings"]:
                pos_name = meaning["partOfSpeech"]
                if word.get(pos_name) is None:
                    word[pos_name] = []
                for definition in meaning["definitions"]:
                    example = definition.get("example")
                    if example and word in example:
                        word[pos_name].append(example)
        return word

    @classmethod
    async def translate(cls, text: str):
        if re.fullmatch(r"""[a-zA-Z-,?.!:"' ]+""", text):
            body = {
                "source": "en",
                "target": "ru"
            }
        elif re.fullmatch(r"""[а-яА-Я-,?.!:"' ]+""", text):
            body = {
                "source": "ru",
                "target": "en"
            }
        else:
            raise ValueError(f"Incorrect text {text} to translate")

        body["q"] = text

        translate_ = cls._translate_cache[text]
        if translate_ is not None:
            return translate_

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
                        data = data["data"]["translations"]["translatedText"]
                    except KeyError:
                        raise KeyError(f"Translate API {cls._translate_host} returned unexpected data {data}\n"
                                       f"Status {status}")
                else:
                    errors.error(f"Translate API returned unexpected code {status}")
                    return
                cls._translate_cache[text] = data
                return data

    @classmethod
    async def _yandex(cls, word: str):
        if re.fullmatch(r"[a-zA-Z-]+", word):
            lang = "en-ru"
        elif re.fullmatch(r"[а-яА-Я-]+", word):
            lang = "ru-en"
        else:
            raise ValueError(f"Incorrect text {word} to yandex translate")

        translate_ = cls._word_data_cache[word]
        if translate_ is not None:
            return translate_

        async with ClientSession() as session:
            async with session.get(
                    f"{cls._yandex_host}&lang={lang}&text={word}",
            ) as response_:
                status = response_.status
                if status == 200:
                    data = await response_.json()
                    try:
                        data = cls._yandex_parsing(data)
                    except KeyError:
                        raise KeyError(f"Yandex dict API {cls._yandex_host} returned unexpected data {data} Status {status}")
                else:
                    errors.error(f"Yandex dict API returned unexpected code {status}")
                    return

                cls._word_data_cache[word] = data
                return data

    @classmethod
    def _yandex_parsing(cls, data: Dict):
        resume = {}
        for pos in data["def"]:
            ts = pos.get("ts")
            if ts:
                resume["ts"] = ts
            resume[pos["pos"]] = {
                "tr": [],
                "syn": [],
            }
            for tr in pos["tr"]:
                resume[pos["pos"]]["tr"].append(tr["text"])
                resume[pos["pos"]]["syn"].extend((mean["text"] for mean in tr.get("mean", ())))

        return resume


w = "span"
e = asyncio.run(SuperEnglishDictionary._audio_and_examples(w))
y = asyncio.run(SuperEnglishDictionary._yandex(w))
with open("e.json", "w", encoding="utf-8") as file:
    json.dump(e, file, indent=4, ensure_ascii=False)

with open("ey.json", "a", encoding="utf-8") as file:
    json.dump(e, file, indent=4, ensure_ascii=False)
    json.dump(y, file, indent=4, ensure_ascii=False)
