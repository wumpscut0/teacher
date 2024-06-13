from typing import List

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from cache import OfferStorage
from database import Session, engine
from database.models import User, Word, WordModel, Base
from core.tools import Emoji


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def insert_user(user_id: str):
    try:
        async with Session.begin() as session:
            await session.execute(insert(User).values(id=user_id))
    except IntegrityError:
        pass


async def select_words() -> List[WordModel]:
    async with Session.begin() as session:
        return [word.as_model() for word in (await session.execute(select(Word))).scalars()]


async def insert_new_words():
    storage = OfferStorage()
    words = []
    for button in storage.offer_copy:
        if button.mark == Emoji.TICK:
            eng, translate = button.text.split(":")
            words.append(Word(eng=eng, translate=translate.split(", ")))
    async with Session.begin() as session:
        session.add_all(words)
    await session.commit()
    storage.offer_copy = None
