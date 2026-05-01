import json
import logging
import random
from app.services.llm.client import call_ollama
from app.services.llm.prompts import build_quiz_prompt
from app.services.llm.validator import parse_json_lenient

logger = logging.getLogger("psc_agent.quiz.generator")


def validate_quiz_question(text: str) -> dict:
    data = parse_json_lenient(text)

    if data is None:
        raise ValueError("Could not parse quiz JSON response")

    if isinstance(data, list):
        data = data[0] if data else {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data).__name__}")

    if not isinstance(data.get("options"), list) or len(data["options"]) != 4:
        raise ValueError(f"Invalid options: {data.get('options')}")

    if data.get("correct_answer") not in data["options"]:
        raise ValueError(f"Correct answer not in options")

    if not data.get("explanation"):
        raise ValueError("Missing explanation")

    if not data.get("question"):
        raise ValueError("Missing question")

    return data


def generate_quiz(articles: list[dict], max_retries: int = 3) -> list[dict] | None:
    questions = []
    used_indices = set()

    for q_num in range(5):
        if len(articles) <= len(used_indices):
            break

        available = [i for i in range(len(articles)) if i not in used_indices]
        idx = random.choice(available)
        used_indices.add(idx)
        article = articles[idx]

        summary = f"Title: {article['title']}\nSummary: {article['summary']}\nCategory: {article['category']}"
        prompt = build_quiz_prompt(summary)

        success = False
        for attempt in range(max_retries + 1):
            try:
                raw = call_ollama(prompt)
                response_text = raw.get("message", {}).get("content", raw.get("response", ""))
                question = validate_quiz_question(response_text)
                questions.append(question)
                logger.info(f"Generated question {q_num + 1}: {question['question'][:60]}")
                success = True
                break
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Failed to generate question {q_num + 1} from article {idx}: {e}")
                else:
                    logger.warning(f"Question {q_num + 1} attempt {attempt + 1} failed: {e}")

        if not success:
            used_indices.discard(idx)

    return questions if questions else None
