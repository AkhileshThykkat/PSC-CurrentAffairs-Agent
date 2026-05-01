from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProcessedArticle(Base):
    __tablename__ = "processed_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_id = Column(Integer, ForeignKey("raw_articles.id"), nullable=False)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    key_points = Column(String, nullable=False)
    category = Column(String, nullable=False)
    importance = Column(String, nullable=False)
    exam_relevance = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
