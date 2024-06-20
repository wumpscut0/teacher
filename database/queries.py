from typing import List

from sqlalchemy import insert, select, delete
from sqlalchemy.exc import IntegrityError

from database import async_session, async_engine
from database.models import User, Word, WordModel, Base


async def create_all():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def insert_user(user_id: str):
    try:
        async with async_session.begin() as session:
            await session.execute(insert(User).values(id=user_id))
        return True
    except IntegrityError:
        return False


async def select_words() -> List[WordModel]:
    async with async_session.begin() as session:
        return [word.as_model() for word in (await session.execute(select(Word))).scalars()]


async def insert_new_words(*words: WordModel):
    for word in words:
        try:
            async with async_session.begin() as session:
                await session.execute(insert(Word).values(**word.model_dump()))
        except IntegrityError:
            pass
    await session.commit()


async def delete_words(*words: str):
    async with async_session.begin() as session:
        for word in words:
            await session.execute(delete(Word).where(Word.word == word))
    await session.commit()
