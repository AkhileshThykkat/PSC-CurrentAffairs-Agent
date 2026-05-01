import json
import logging
from datetime import datetime, date
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.raw_article import RawArticle
from app.models.processed_article import ProcessedArticle
from app.models.quiz import Quiz
from app.services.scraper.rss import scrape_feeds
from app.services.scraper.html import fetch_article, extract_article_text, extract_image
from app.services.dedup.semantic import is_semantic_duplicate, add_embedding, clear_index, build_index_from_texts
from app.services.llm.validator import process_article
from app.services.classifier.filter import compute_psc_score, determine_psc_category, should_keep
from app.services.quiz.generator import generate_quiz

logger = logging.getLogger("psc_agent.workers.tasks")


@celery_app.task(bind=True, max_retries=3)
def scrape_feeds_task(self):
    try:
        logger.info("Starting feed scraping")
        stats = scrape_feeds()
        logger.info(f"Scraping complete: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task
def fetch_full_articles_task():
    db = SessionLocal()
    stats = {"fetched": 0, "errors": 0}

    try:
        raw_articles = db.query(RawArticle).filter(RawArticle.content == "").all()

        for article in raw_articles:
            try:
                html = fetch_article(article.url)
                if html:
                    article.content = extract_article_text(html)
                    stats["fetched"] += 1
            except Exception as e:
                logger.error(f"Error fetching {article.url}: {e}")
                stats["errors"] += 1

        db.commit()
        logger.info(f"Full article fetch complete: {stats}")
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during article fetch: {e}")
    finally:
        db.close()

    return stats


@celery_app.task
def dedup_task():
    db = SessionLocal()
    stats = {"checked": 0, "removed": 0}

    try:
        raw_articles = db.query(RawArticle).all()
        articles_with_content = [a for a in raw_articles if a.content and a.content.strip()]

        clear_index()

        to_remove = []
        for article in articles_with_content:
            stats["checked"] += 1
            text = article.title + " " + article.content[:300]

            if is_semantic_duplicate(text):
                to_remove.append(article)
                stats["removed"] += 1
            else:
                add_embedding(text)

        for article in to_remove:
            db.delete(article)

        db.commit()
        logger.info(f"Dedup complete: {stats}")
    except Exception as e:
        db.rollback()
        logger.error(f"Dedup failed: {e}")
    finally:
        db.close()

    return stats


@celery_app.task
def process_articles_task():
    db = SessionLocal()
    stats = {"processed": 0, "skipped": 0, "filtered": 0, "errors": 0}

    try:
        unprocessed = (
            db.query(RawArticle)
            .outerjoin(ProcessedArticle, RawArticle.id == ProcessedArticle.raw_id)
            .filter(ProcessedArticle.id == None)
            .filter(RawArticle.content != "")
            .all()
        )

        for article in unprocessed:
            try:
                text = article.title + "\n\n" + article.content
                result = process_article(text)

                if not result:
                    stats["skipped"] += 1
                    continue

                psc_score, psc_topics = compute_psc_score(article.title, article.content or "")
                if psc_topics:
                    result["category"] = determine_psc_category(psc_topics)
                result["psc_score"] = psc_score
                result["psc_topics"] = psc_topics

                if not should_keep(result, []):
                    stats["filtered"] += 1
                    continue

                image_url = None
                if article.content:
                    try:
                        html = fetch_article(article.url)
                        if html:
                            image_url = extract_image(html, article.url)
                    except Exception:
                        pass

                processed = ProcessedArticle(
                    raw_id=article.id,
                    title=result["title"],
                    summary=result["summary"],
                    key_points=json.dumps(result["key_points"]),
                    category=result["category"],
                    importance=result["importance"],
                    exam_relevance=result.get("exam_relevance"),
                    image_url=image_url,
                )
                db.add(processed)
                db.flush()
                stats["processed"] += 1

            except Exception as e:
                logger.error(f"Error processing article {article.id}: {e}")
                stats["errors"] += 1

        db.commit()
        logger.info(f"Article processing complete: {stats}")
    except Exception as e:
        db.rollback()
        logger.error(f"Processing failed: {e}")
    finally:
        db.close()

    return stats


@celery_app.task
def generate_daily_quiz_task():
    db = SessionLocal()
    today = datetime.now().date()

    try:
        existing = db.query(Quiz).filter(Quiz.date == today).first()
        if existing:
            logger.info("Quiz already exists for today, skipping")
            return {"status": "skipped", "reason": "quiz already exists"}

        articles = (
            db.query(ProcessedArticle)
            .all()
        )

        if not articles:
            logger.info("No articles available for quiz generation")
            return {"status": "skipped", "reason": "no articles"}

        article_dicts = [
            {"title": a.title, "summary": a.summary, "category": a.category}
            for a in articles
        ]

        quiz_questions = generate_quiz(article_dicts)
        if not quiz_questions:
            return {"status": "failed", "reason": "LLM generation failed"}

        for q in quiz_questions:
            quiz = Quiz(
                question=q["question"],
                options=json.dumps(q["options"]),
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                date=today,
            )
            db.add(quiz)

        db.commit()
        logger.info(f"Generated {len(quiz_questions)} quiz questions for {today}")
        return {"status": "success", "count": len(quiz_questions)}

    except Exception as e:
        db.rollback()
        logger.error(f"Quiz generation failed: {e}")
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task
def run_full_pipeline():
    logger.info("Starting full pipeline")

    scrape_feeds_task.delay()
    fetch_full_articles_task.delay()
    dedup_task.delay()
    process_articles_task.delay()

    logger.info("Full pipeline tasks dispatched")
    return {"status": "dispatched"}
