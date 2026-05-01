import json
import ast
import re
import logging
from app.services.llm.client import call_ollama
from app.services.llm.prompts import build_article_prompt

logger = logging.getLogger("psc_agent.llm.validator")

REQUIRED_FIELDS = {"title", "summary", "key_points", "category", "importance", "exam_relevance"}
VALID_CATEGORIES = {"Kerala", "India", "International"}
VALID_IMPORTANCE = {"HIGH", "MEDIUM", "LOW"}


def extract_json_block(text: str) -> str:
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?\s*\n?", "", text)
    text = re.sub(r"```\s*$", "", text)

    # Strip HTML tags if the model outputs HTML
    if "<" in text and ">" in text:
        text = re.sub(r"<[^>]+>", "", text)

    text = text.strip()

    # Find the outermost JSON object or array
    for open_char, close_char in [("{", "}"), ("[", "]")]:
        start = text.find(open_char)
        if start == -1:
            continue
        # Track nesting depth to find the matching close char
        depth = 0
        for i, c in enumerate(text[start:], start):
            if c == open_char:
                depth += 1
            elif c == close_char:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]

    return text


def parse_json_lenient(text: str) -> dict | list:
    text = extract_json_block(text)

    # 1. Standard JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Replace single quotes used as string delimiters (not apostrophes inside strings)
    # Match single quotes at the start/end of values or keys
    try:
        fixed = re.sub(r"(?<=\s|:|\[|,)'([^']*)'(?=\s|,|\]|\}|:)", r'"\1"', text)
        # Also handle cases where the whole thing uses single quotes
        if "'" in fixed and '"' not in fixed:
            fixed = text.replace("'", '"')
        return json.loads(fixed)
    except (json.JSONDecodeError, ValueError):
        pass

    # 3. Python literal eval (handles single quotes, trailing commas)
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        pass

    return None


def fix_key_points(data: dict) -> dict:
    if not isinstance(data.get("key_points"), list) or len(data["key_points"]) < 2:
        points = data.get("key_points", [])
        summary = data.get("summary", "")

        if isinstance(points, list) and len(points) == 1 and summary:
            sentences = [s.strip() for s in re.split(r"[.!?]+", summary) if len(s.strip()) > 10]
            if len(sentences) >= 2:
                data["key_points"] = sentences[:3]
            else:
                data["key_points"] = [points[0], summary[:150]]
        elif isinstance(points, str):
            sentences = [s.strip() for s in re.split(r"[.!?]+", points) if len(s.strip()) > 10]
            data["key_points"] = sentences[:3] if sentences else [points]
        elif summary:
            sentences = [s.strip() for s in re.split(r"[.!?]+", summary) if len(s.strip()) > 10]
            data["key_points"] = sentences[:3] if sentences else [summary[:150]]
        else:
            data["key_points"] = [data.get("title", "No summary available")]

    return data


def validate_llm_response(text: str) -> dict:
    logger.debug(f"Raw LLM output (first 500 chars): {text[:500]}")
    logger.debug(f"Raw LLM output length: {len(text)}")

    data = parse_json_lenient(text)

    if data is None:
        raise ValueError(f"Could not parse JSON response. Raw output: {text[:300]}")

    if isinstance(data, list):
        data = data[0] if data else {}

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict, got {type(data).__name__}: {str(data)[:200]}")

    missing = REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Missing fields: {missing}. Got keys: {list(data.keys())}. Raw: {text[:300]}")

    extra = set(data.keys()) - REQUIRED_FIELDS
    for field in extra:
        del data[field]

    if data["category"] not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category: {data['category']}")

    if data["importance"] not in VALID_IMPORTANCE:
        raise ValueError(f"Invalid importance: {data['importance']}")

    data = fix_key_points(data)

    if not (2 <= len(data["key_points"]) <= 5):
        raise ValueError(f"key_points must have 2-5 items, got {len(data['key_points'])}")

    return data


def process_article(article_text: str, max_retries: int = 3) -> dict | None:
    for attempt in range(max_retries + 1):
        try:
            prompt = build_article_prompt(article_text)
            raw = call_ollama(prompt)
            response_text = raw.get("response", "")
            return validate_llm_response(response_text)
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"LLM failed after {max_retries} retries: {e}")
                return None
            logger.warning(f"LLM attempt {attempt + 1} failed, retrying: {e}")

    return None
