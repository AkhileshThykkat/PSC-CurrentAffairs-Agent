import logging

logger = logging.getLogger("psc_agent.classifier.filter")

IMPORTANCE_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def should_keep(article: dict, daily_india_articles: list[dict]) -> bool:
    category = article.get("category", "")
    importance = article.get("importance", "LOW")

    if category == "Kerala":
        return True

    elif category == "India":
        sorted_articles = sorted(
            daily_india_articles,
            key=lambda a: IMPORTANCE_RANK.get(a.get("importance", "LOW"), 0),
            reverse=True,
        )
        keep_count = max(1, int(len(sorted_articles) * 0.70))
        return any(a is article for a in sorted_articles[:keep_count])

    elif category == "International":
        return importance == "HIGH"

    return False
