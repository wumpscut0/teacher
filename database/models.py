from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    ...


# class UserDictionary(Base):
#     __tablename__ = "user_dictionary"
#     user_id = Column(String, ForeignKey("user.id"))
#     word_id = Column(String, ForeignKey("dictionary.id"))


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
    rus: str


class Word(Base):
    __tablename__ = "word"
    eng = Column(String, nullable=False, primary_key=True)
    rus = Column(String, nullable=False, primary_key=True)

    def as_model(self):
        return WordModel(**{c.name: getattr(self, c.name) for c in self.__table__.columns})
