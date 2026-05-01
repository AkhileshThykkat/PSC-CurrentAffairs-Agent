import json
import logging
import re
from app.services.llm.client import call_ollama
from app.services.llm.prompts import build_article_prompt

logger = logging.getLogger("psc_agent.llm.validator")

REQUIRED_FIELDS = {"title", "summary", "key_points", "category", "importance", "exam_relevance"}
VALID_CATEGORIES = {"Kerala", "India", "International"}
VALID_IMPORTANCE = {"HIGH", "MEDIUM", "LOW"}


def extract_json_from_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def validate_llm_response(text: str) -> dict:
    cleaned = extract_json_from_response(text)
    data = json.loads(cleaned)

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Missing fields: {missing}")

    extra = set(data.keys()) - REQUIRED_FIELDS
    if extra:
        raise ValueError(f"Unexpected fields: {extra}")

    if data["category"] not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category: {data['category']}")

    if data["importance"] not in VALID_IMPORTANCE:
        raise ValueError(f"Invalid importance: {data['importance']}")

    if not isinstance(data["key_points"], list):
        raise ValueError("key_points must be a list")

    if not (2 <= len(data["key_points"]) <= 5):
        raise ValueError(f"key_points must have 2-5 items, got {len(data['key_points'])}")

    return data


def process_article(article_text: str, max_retries: int = 2) -> dict | None:
    for attempt in range(max_retries + 1):
        try:
            prompt = build_article_prompt(article_text)
            raw = call_ollama(prompt)
            response_text = raw.get("response", "")
            return validate_llm_response(response_text)
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"LLM failed after {max_retries} retries for article: {e}")
                return None
            logger.warning(f"LLM attempt {attempt + 1} failed, retrying: {e}")

    return None
