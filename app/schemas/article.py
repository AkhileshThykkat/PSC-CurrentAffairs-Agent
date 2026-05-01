from datetime import datetime
from pydantic import BaseModel


class ArticleResponse(BaseModel):
    id: int
    title: str
    summary: str
    key_points: list[str]
    category: str
    importance: str
    exam_relevance: str | None
    image_url: str | None
    source: str
    url: str
    published_at: datetime | None
    created_at: datetime | None


class ArticleListResponse(BaseModel):
    count: int
    articles: list[ArticleResponse]


class RawArticleResponse(BaseModel):
    id: int
    title: str
    content: str | None
    source: str
    url: str
    published_at: datetime | None
    created_at: datetime | None
