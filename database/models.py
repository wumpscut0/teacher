from datetime import datetime
from typing import List

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, ARRAY
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    ...


class EnglishRun(Base):
    __tablename__ = "english_run"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    result = Column(Integer, nullable=False)
    dictionary_size = Column(Integer, nullable=False)
    completed_datetime = Column(DateTime, default=datetime.now())


class User(Base):
    __tablename__ = "user"
    id = Column(String, primary_key=True)


class WordModel(BaseModel):
    eng: str
    translate: List[str]


class Word(Base):
    __tablename__ = "word"
    eng = Column(String, nullable=False, primary_key=True)
    translate = Column(ARRAY(String), nullable=False)

    def as_model(self):
        return WordModel(**{c.name: getattr(self, c.name) for c in self.__table__.columns})
