import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import init_db
from app.services.scraper.rss import scrape_feeds
from app.services.scraper.html import fetch_article, extract_article_text, extract_image
from app.services.dedup.semantic import is_semantic_duplicate, add_embedding
from app.services.llm.validator import process_article
from app.services.classifier.filter import compute_psc_score, determine_psc_category, should_keep
from app.services.quiz.generator import generate_quiz
from app.db.session import SessionLocal
from app.models.raw_article import RawArticle
from app.models.processed_article import ProcessedArticle
from app.models.quiz import Quiz
import json
from datetime import datetime, timezone, date

init_db()

print("=" * 50)
print("PSC Current Affairs Agent - Manual Pipeline Run")
print("=" * 50)

print("\n[1/5] Scraping RSS feeds...")
stats = scrape_feeds()
print(f"  Total entries: {stats['total_entries']}")
print(f"  New articles: {stats['new_articles']}")
print(f"  Skipped duplicates: {stats['skipped_duplicates']}")

print("\n[2/5] Fetching full article content...")
db = SessionLocal()
fetched = 0
errors = 0
articles_without_content = db.query(RawArticle).filter(RawArticle.content == "").all()

for article in articles_without_content:
    try:
        html = fetch_article(article.url)
        if html:
            article.content = extract_article_text(html)
            fetched += 1
    except Exception as e:
        errors += 1

db.commit()
print(f"  Fetched: {fetched}, Errors: {errors}")

print("\n[3/5] Running deduplication...")
all_articles = db.query(RawArticle).all()
removed = 0

# Only keep articles that have content (already fetched)
articles_with_content = [a for a in all_articles if a.content and a.content.strip()]

# Rebuild FAISS index from scratch using only articles with content
if articles_with_content:
    from app.services.dedup.semantic import build_index_from_texts, clear_index
    clear_index()

    # Process in order: add to index, if duplicate found, remove
    seen_texts = []
    to_remove = []
    for article in articles_with_content:
        text = article.title + " " + article.content[:300]
        from app.services.dedup.semantic import is_semantic_duplicate, add_embedding
        if is_semantic_duplicate(text):
            to_remove.append(article)
            removed += 1
        else:
            add_embedding(text)
            seen_texts.append(text)

    for article in to_remove:
        db.delete(article)
else:
    print("  No articles with content to dedup.")

db.commit()
print(f"  Removed semantic duplicates: {removed}")

print("\n[4/5] Processing articles with PSC relevance scoring...")
unprocessed = (
    db.query(RawArticle)
    .outerjoin(ProcessedArticle, RawArticle.id == ProcessedArticle.raw_id)
    .filter(ProcessedArticle.id == None)
    .filter(RawArticle.content != "")
    .all()
)

processed_count = 0
filtered_count = 0
skipped_count = 0
all_processed_articles = []

for article in unprocessed:
    text = article.title + "\n\n" + article.content
    result = process_article(text)
    if not result:
        skipped_count += 1
        continue

    psc_score, psc_topics = compute_psc_score(article.title, article.content or "")
    if psc_topics:
        result["category"] = determine_psc_category(psc_topics)
    result["psc_score"] = psc_score
    result["psc_topics"] = psc_topics

    if not should_keep(result, []):
        filtered_count += 1
        continue

    image_url = None
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
    all_processed_articles.append({
        "title": result["title"],
        "summary": result["summary"],
        "category": result["category"],
        "psc_score": psc_score,
        "psc_topics": psc_topics,
    })
    processed_count += 1

db.commit()
print(f"  Processed: {processed_count}, Filtered (low PSC relevance): {filtered_count}, LLM skipped: {skipped_count}")
if all_processed_articles:
    print(f"  Topics covered: {', '.join(set(t for a in all_processed_articles for t in a['psc_topics']))}")

print("\n[5/5] Generating daily quiz...")
today = date.today()
existing_quiz = db.query(Quiz).filter(Quiz.date == today).first()

if existing_quiz:
    print("  Quiz already exists for today, skipping.")
else:
    if all_processed_articles:
        quiz_questions = generate_quiz(all_processed_articles)
        if quiz_questions:
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
            print(f"  Generated {len(quiz_questions)} quiz questions.")
        else:
            print("  Quiz generation failed.")
    else:
        print("  No articles available for quiz generation.")

db.close()
print("\n" + "=" * 50)
print("Pipeline complete! Visit http://localhost:8000 to view results.")
print("=" * 50)
