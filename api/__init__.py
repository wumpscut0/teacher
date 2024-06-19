import asyncio
import json
import os
import re
from typing import List

from aiohttp import ClientSession
from cache import TranslateCache, WordEntriesCache, YandexDictCache
from core.tools.loggers import info, errors


class SuperEnglishDictionary:
    _entries_host = "https://api.dictionaryapi.dev"
    _entries_cache = WordEntriesCache()

    _translate_host = "https://deep-translate1.p.rapidapi.com"
    _translate_headers = {
        "x-rapidapi-key": os.getenv("RAPID_TRANSLATE"),
        "x-rapidapi-host": "deep-translate1.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    _translate_cache = TranslateCache()

    _yandex_host = f"https://dictionary.yandex.net/api/v1/dicservice.json/lookup?key={os.getenv("YANDEX_DICT")}"
    _yandex_cache = YandexDictCache()

    @classmethod
    async def entries(cls, word: str):
        if not re.fullmatch(r"[a-zA-Z-]+", word):
            raise ValueError(f"Incorrect word {word} for entries")

        entries_ = cls._entries_cache[word]
        if entries_ is not None:
            return entries_

        path = f"{cls._entries_host}/api/v2/entries/en/{word}"
        async with ClientSession() as session:
            async with session.get(path) as response_:
                status = response_.status
                if status == 200:
                    data = await response_.json()
                    try:
                        data = cls._entries_parsing(data)
                    except KeyError:
                        info.critical(f"Entries API {path} returned unexpected data {data}\n"
                                      f"Status {status}")
                        return
                elif status == 404:
                    info.warning(f"No entries for word {word}")
                    return
                else:
                    errors.error(f"Entries API returned unexpected code {status}")
                    return

                cls._entries_cache[word] = data
                return data

    @classmethod
    def _entries_parsing(cls, entries: List):
        word = {
            "phonetic": str,
            "audios": [],
            "parts_of_speeches": {},
            "full_response": entries
        }
        for entry in entries:
            phonetic = entry.get("phonetic")
            if phonetic:
                word["phonetic"] = phonetic
            for phonetic in entry["phonetics"]:
                audio = phonetic.get("audio")
                if audio:
                    word["audios"].append(audio)

            for meaning in entry["meanings"]:
                pos_name = meaning["partOfSpeech"]
                if word["parts_of_speeches"].get(pos_name) is None:
                    word["parts_of_speeches"][pos_name] = {
                        "examples": [],
                        "synonyms": []
                    }
                for definition in meaning["definitions"]:
                    example = definition.get("example")
                    if example:
                        word["parts_of_speeches"][pos_name]["examples"].append(example)
                word["parts_of_speeches"][pos_name]["synonyms"].extend(meaning["synonyms"])

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
    async def yandex(cls, text: str):
        if re.fullmatch(r"""[a-zA-Z-,?.!:"' ]+""", text):
            lang = "en-ru"

        elif re.fullmatch(r"""[а-яА-Я-,?.!:"' ]+""", text):
            lang = "ru-en"
        else:
            raise ValueError(f"Incorrect text {text} to yandex translate")

        # translate_ = cls._yandex_cache[text]
        # if translate_ is not None:
        #     return translate_

        async with ClientSession() as session:
            async with session.get(
                    f"{cls._yandex_host}&lang={lang}&text={text}",
            ) as response_:
                status = response_.status
                if status == 200:
                    data = await response_.json()
                    try:
                        pass
                    except KeyError:
                        raise KeyError(f"Yandex dict API {cls._yandex_host} returned unexpected data {data}\n"
                                       f"Status {status}")
                else:
                    errors.error(f"Yandex dict API returned unexpected code {status}")
                    return

                cls._yandex_cache[text] = data
                return data

w = ("span"
     "")
with open("y.json", "w", encoding="utf-8") as file:
    json.dump(asyncio.run(SuperEnglishDictionary.yandex(w)), file, indent=4, ensure_ascii=False)

x =   k
