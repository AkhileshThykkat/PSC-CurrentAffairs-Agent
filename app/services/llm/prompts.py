SYSTEM_PROMPT = """You are a Kerala PSC exam-focused news processor.

Convert the following article into a strict JSON object. Output ONLY valid JSON. No explanation. No markdown. No code blocks. No backticks.

Article:
{article_text}

Required JSON format (do NOT change field names):
{{
  "title": "concise title under 15 words",
  "summary": "max 3 lines, focus on facts: who, what, when, where, numbers, names",
  "key_points": ["fact 1", "fact 2", "fact 3"],
  "category": "Kerala",
  "importance": "HIGH",
  "exam_relevance": "one sentence on PSC relevance"
}}

Rules:
- category MUST be exactly one of: Kerala, India, International
- Kerala government schemes, appointments, awards, sports, geography = Kerala
- National news with PSC relevance = India
- International summits, global events = International
- importance MUST be exactly one of: HIGH, MEDIUM, LOW
- key_points MUST be exactly 3 short factual bullet points
- Use double quotes for all strings. No trailing commas.
- Focus on: names, positions, dates, places, numbers, awards, scheme names
- If article is a movie review, crime report, or weather alert, set importance to LOW
- Output the JSON object and nothing else"""


QUIZ_PROMPT = """You are a Kerala PSC exam question setter.

Based ONLY on the following news, generate ONE MCQ question in Kerala PSC style.

News:
{summaries}

Kerala PSC question style examples:
- "Who was appointed as the new Governor of Kerala?"
- "Which scheme was launched by the Kerala government for welfare of farmers?"
- "Which award was conferred on [person] in 2026?"
- "Where was the [event] held in 2026?"
- "Which country hosted the [tournament] in 2026?"

Rules:
- Generate exactly ONE question
- Question must test a FACT from the news (name, place, date, number, scheme, award)
- 4 options: "A. ...", "B. ...", "C. ...", "D. ..."
- 1 correct answer matching one option exactly
- Keep options concise and plausible
- Use double quotes. No markdown. No code blocks.

Output ONLY a JSON object:
{{
  "question": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct_answer": "A. ...",
  "explanation": "one sentence"
}}"""


def build_article_prompt(article_text: str) -> str:
    return SYSTEM_PROMPT.format(article_text=article_text)


def build_quiz_prompt(summaries: str) -> str:
    return QUIZ_PROMPT.format(summaries=summaries)
