import json
import logging
from app.services.llm.client import call_ollama
from app.services.llm.prompts import build_quiz_prompt

logger = logging.getLogger("psc_agent.quiz.generator")


def validate_quiz_response(text: str) -> list[dict]:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    data = json.loads(cleaned)

    if not isinstance(data, list):
        raise ValueError("Quiz response must be a JSON array")

    validated = []
    for item in data:
        if not isinstance(item.get("options"), list) or len(item["options"]) != 4:
            raise ValueError(f"Invalid options in question: {item.get('question', 'unknown')}")

        if item.get("correct_answer") not in item["options"]:
            raise ValueError(f"Correct answer not in options: {item.get('question', 'unknown')}")

        if not item.get("explanation"):
            raise ValueError(f"Missing explanation: {item.get('question', 'unknown')}")

        validated.append(item)

    return validated


def generate_quiz(summaries: str, max_retries: int = 2) -> list[dict] | None:
    for attempt in range(max_retries + 1):
        try:
            prompt = build_quiz_prompt(summaries)
            raw = call_ollama(prompt)
            response_text = raw.get("response", "")
            return validate_quiz_response(response_text)
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Quiz generation failed after {max_retries} retries: {e}")
                return None
            logger.warning(f"Quiz generation attempt {attempt + 1} failed: {e}")

    return None
