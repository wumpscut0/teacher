from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


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

    word = relationship("UserWord")

########################################################################################################################


class Word(Base):
    __tablename__ = "word"
    word = Column(String, primary_key=True, unique=True)

    def as_str(self):
        for c in self.__table__.columns:
            return getattr(self, c.name)


########################################################################################################################

class Knowledge(BaseModel):
    translate: str
    levenshtein_distances: list


class WordUserKnowledge(Base):
    __tablename__ = "user_word_knowledge"
    user_id = Column(String, ForeignKey("user.id"), nullable=False, primary_key=True)
    word = Column(String, ForeignKey("word.word"), nullable=False, primary_key=True)
    knowledge = Column(JSON, default={})

    def as_model(self):
        return Knowledge(**{c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in ("user_id", "word")})
