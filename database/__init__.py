import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


async_engine = create_async_engine(os.getenv("DATABASE"))
async_session = async_sessionmaker(async_engine)
