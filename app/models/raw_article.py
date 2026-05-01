from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.db.base import Base


class RawArticle(Base):
    __tablename__ = "raw_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=True)
    source = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    published_at = Column(DateTime, nullable=True)
    hash = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
