import re
import logging
from app.services.classifier.psc_taxonomy import (
    PSC_HIGH_PRIORITY,
    PSC_LOW_PRIORITY,
    PSC_TOPIC_LABELS,
)

logger = logging.getLogger("psc_agent.classifier.filter")

IMPORTANCE_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def compute_psc_score(title: str, content: str) -> tuple[float, list[str]]:
    """Score an article for PSC relevance. Returns (score, matched_topics)."""
    text = (title + " " + content[:500]).lower()
    score = 0.0
    matched_topics = []

    for topic, keywords in PSC_HIGH_PRIORITY.items():
        matches = sum(1 for kw in keywords if kw.lower() in text)
        if matches > 0:
            score += matches * 2
            matched_topics.append(topic)

    for keywords in PSC_LOW_PRIORITY.values():
        matches = sum(1 for kw in keywords if kw.lower() in text)
        if matches > 0:
            score -= matches * 1.5

    if any(kw in text for kw in ["review", "box office", "cinema", "movie review"]):
        score -= 5

    if any(kw in text for kw in ["murder", "killed", "stabbed", "suicide", "arrested"]):
        score -= 3

    if any(kw in text for kw in ["yellow alert", "red alert", "orange alert", "rains", "cyclone"]):
        score -= 4

    if any(kw in text for kw in ["traffic", "strike", "hartal", "protest", "rally", "bandh"]):
        score -= 2

    if "kerala" in text:
        score += 1

    if any(kw in text for kw in ["first in", "first in india", "first in kerala", "inaugurated", "launched"]):
        score += 3

    return min(max(score, 0), 20), matched_topics


def determine_psc_category(matched_topics: list[str]) -> str:
    """Map matched PSC topics to one of the standard categories."""
    kerala_topics = {"appointments", "schemes_policies", "geography_kerala", "economics"}
    india_topics = {"constitutional_governance", "economics", "science_technology", "sports", "awards_honours"}
    intl_topics = {"international"}

    if any(t in kerala_topics for t in matched_topics):
        return "Kerala"
    if any(t in india_topics for t in matched_topics):
        return "India"
    if any(t in intl_topics for t in matched_topics):
        return "International"
    return "India"


def should_keep(article: dict, daily_india_articles: list[dict]) -> bool:
    category = article.get("category", "")
    importance = article.get("importance", "LOW")
    psc_score = article.get("psc_score", 0)

    if psc_score < 2:
        return False

    if category == "Kerala":
        return psc_score >= 3

    elif category == "India":
        if psc_score < 5:
            return False
        sorted_articles = sorted(
            daily_india_articles,
            key=lambda a: IMPORTANCE_RANK.get(a.get("importance", "LOW"), 0),
            reverse=True,
        )
        keep_count = max(1, int(len(sorted_articles) * 0.70))
        return any(a is article for a in sorted_articles[:keep_count])

    elif category == "International":
        return importance == "HIGH" and psc_score >= 5

    return False
