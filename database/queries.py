from typing import List

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from database import Session, engine
from database.models import User, Word, WordModel, Base


async def create_all():
    async with engine.connect() as conn:
        conn.run_sync(Base.metadata.create_all)


async def insert_user(user_id: str):
    try:
        async with Session.begin() as session:
            await session.execute(insert(User).values(id=user_id))
    except IntegrityError:
        pass


async def select_words() -> List[WordModel]:
    async with Session.begin() as session:
        return [word.as_model() for word in (await session.execute(select(Word))).scalars()]
