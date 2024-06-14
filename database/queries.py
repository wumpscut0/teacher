from typing import List

from sqlalchemy import insert, select, delete
from sqlalchemy.exc import IntegrityError

from cache import EnglishRunStorage
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
        return True
    except IntegrityError:
        return False


async def select_words() -> List[WordModel]:
    async with Session.begin() as session:
        return [word.as_model() for word in (await session.execute(select(Word))).scalars()]


async def insert_new_words(rewrite=False):
    storage = EnglishRunStorage()
    if rewrite:
        async with Session.begin() as session:
            await session.execute(delete(Word))
        session.commit()
    for button in storage.edit:
        try:
            async with Session.begin() as session:
                if button.mark == Emoji.OK:
                    eng, translate = button.text.split(":")
                await session.execute(insert(Word).values(eng=eng.lstrip(f"{Emoji.OK} "), translate=translate.split(", ")))
        except IntegrityError:
            pass

    await session.commit()
    storage.edit = None
