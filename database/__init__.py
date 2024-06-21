import json
import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


async_engine = create_async_engine(
    os.getenv("DATABASE"),
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False)
)
async_session = async_sessionmaker(async_engine)
