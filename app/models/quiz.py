from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, DateTime, Date
from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(String, nullable=False)
    options = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=utcnow)
