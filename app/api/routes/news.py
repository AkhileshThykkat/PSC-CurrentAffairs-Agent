import json
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api.deps import get_db
from app.models.processed_article import ProcessedArticle
from app.models.raw_article import RawArticle
from app.schemas.article import ArticleResponse, ArticleListResponse

logger = logging.getLogger("psc_agent.api.news")

router = APIRouter(prefix="/api/news", tags=["news"])


def article_to_response(pa: ProcessedArticle, ra: RawArticle) -> ArticleResponse:
    return ArticleResponse(
        id=pa.id,
        title=pa.title,
        summary=pa.summary,
        key_points=json.loads(pa.key_points),
        category=pa.category,
        importance=pa.importance,
        exam_relevance=pa.exam_relevance,
        image_url=pa.image_url,
        source=ra.source,
        url=ra.url,
        published_at=ra.published_at,
        created_at=pa.created_at,
    )


def today_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/today", response_model=ArticleListResponse)
def get_today_news(db: Session = Depends(get_db)):
    cutoff = today_start()
    articles = (
        db.query(ProcessedArticle, RawArticle)
        .join(RawArticle, ProcessedArticle.raw_id == RawArticle.id)
        .filter(ProcessedArticle.created_at >= cutoff)
        .order_by(desc(ProcessedArticle.created_at))
        .all()
    )
    return ArticleListResponse(
        count=len(articles),
        articles=[article_to_response(pa, ra) for pa, ra in articles],
    )


@router.get("", response_model=ArticleListResponse)
def get_news(
    days: int = Query(default=1, ge=1, le=365),
    category: str | None = Query(default=None),
    importance: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    cutoff = now_utc() - timedelta(days=days)
    query = (
        db.query(ProcessedArticle, RawArticle)
        .join(RawArticle, ProcessedArticle.raw_id == RawArticle.id)
        .filter(ProcessedArticle.created_at >= cutoff)
    )

    if category:
        query = query.filter(ProcessedArticle.category == category)
    if importance:
        query = query.filter(ProcessedArticle.importance == importance)

    articles = query.order_by(desc(ProcessedArticle.created_at)).all()
    return ArticleListResponse(
        count=len(articles),
        articles=[article_to_response(pa, ra) for pa, ra in articles],
    )


@router.get("/{article_id}")
def get_article(article_id: int, db: Session = Depends(get_db)):
    result = (
        db.query(ProcessedArticle, RawArticle)
        .join(RawArticle, ProcessedArticle.raw_id == RawArticle.id)
        .filter(ProcessedArticle.id == article_id)
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="Article not found")
    pa, ra = result
    return article_to_response(pa, ra)
