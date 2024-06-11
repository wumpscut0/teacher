import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


engine = create_async_engine(os.getenv("DATABASE"))
Session = async_sessionmaker(engine)
