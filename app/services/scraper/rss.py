import hashlib
import logging
from datetime import datetime
from feedparser import parse
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.raw_article import RawArticle

logger = logging.getLogger("psc_agent.scraper.rss")

RSS_FEEDS = [
    "https://www.thehindu.com/news/national/kerala/feeder/default.rss",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://www.thehindu.com/news/international/feeder/default.rss",
    "https://www.mathrubhumi.com/rss/news.xml",
    "https://www.manoramaonline.com/rss/news.xml",
    "https://indianexpress.com/section/india/feed/",
    "https://timesofindia.indiatimes.com/rss/breaking-news",
    "https://feeds.feedburner.com/ndtv/LHdn",
]

SOURCE_MAP = {
    "thehindu.com": "The Hindu",
    "mathrubhumi.com": "Mathrubhumi",
    "manoramaonline.com": "Manorama Online",
    "indianexpress.com": "Indian Express",
    "timesofindia.indiatimes.com": "Times of India",
    "ndtv.com": "NDTV",
}


def compute_hash(title: str, content: str) -> str:
    return hashlib.sha256((title + content[:500]).encode("utf-8")).hexdigest()


def get_source_name(url: str) -> str:
    for domain, name in SOURCE_MAP.items():
        if domain in url:
            return name
    return "Unknown"


def parse_published(entry) -> datetime | None:
    try:
        return datetime(*entry.published_parsed[:6])
    except (AttributeError, TypeError, ValueError):
        return None


def scrape_feeds() -> dict:
    db = SessionLocal()
    stats = {"total_entries": 0, "new_articles": 0, "skipped_duplicates": 0, "errors": 0}
    seen_urls = set()
    seen_hashes = set()

    try:
        existing_urls = {u[0] for u in db.query(RawArticle.url).all()}
        existing_hashes = {h[0] for h in db.query(RawArticle.hash).all()}
        seen_urls.update(existing_urls)
        seen_hashes.update(existing_hashes)

        for feed_url in RSS_FEEDS:
            try:
                feed = parse(feed_url)
                source_name = get_source_name(feed_url)
                logger.info(f"Fetching feed: {feed_url} ({source_name})")

                for entry in feed.entries:
                    stats["total_entries"] += 1
                    title = entry.get("title", "").strip()
                    url = entry.get("link", "").strip()
                    content = entry.get("summary", entry.get("description", "")).strip()
                    published_at = parse_published(entry)

                    if not title or not url:
                        continue

                    article_hash = compute_hash(title, content)

                    if url in seen_urls or article_hash in seen_hashes:
                        stats["skipped_duplicates"] += 1
                        continue

                    seen_urls.add(url)
                    seen_hashes.add(article_hash)

                    article = RawArticle(
                        title=title,
                        content=content,
                        source=source_name,
                        url=url,
                        published_at=published_at,
                        hash=article_hash,
                    )
                    db.add(article)
                    stats["new_articles"] += 1

            except Exception as e:
                logger.error(f"Error fetching feed {feed_url}: {e}")
                stats["errors"] += 1

        db.commit()
        logger.info(f"Scrape complete: {stats}")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during scrape: {e}")
        raise
    finally:
        db.close()

    return stats
