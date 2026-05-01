import logging
from app.db.session import SessionLocal
from app.models.raw_article import RawArticle

logger = logging.getLogger("psc_agent.dedup.exact")


def get_duplicate_hashes() -> set[str]:
    db = SessionLocal()
    try:
        hashes = db.query(RawArticle.hash).all()
        return {h[0] for h in hashes}
    finally:
        db.close()


def get_duplicate_urls() -> set[str]:
    db = SessionLocal()
    try:
        urls = db.query(RawArticle.url).all()
        return {u[0] for u in urls}
    finally:
        db.close()
