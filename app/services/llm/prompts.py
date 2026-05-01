SYSTEM_PROMPT = """You are a Kerala PSC exam-focused news processor.

Convert the following article into a strict JSON object. Output ONLY valid JSON. No explanation. No markdown. No code blocks. No backticks.

Article:
{article_text}

Required JSON format (do NOT change field names):
{{
  "title": "concise title under 15 words",
  "summary": "max 3 lines, plain sentences, focus on facts",
  "key_points": ["point 1", "point 2", "point 3"],
  "category": "Kerala",
  "importance": "HIGH",
  "exam_relevance": "one sentence on why this is relevant for PSC exams"
}}

Rules:
- category MUST be exactly one of: Kerala, India, International
- importance MUST be exactly one of: HIGH, MEDIUM, LOW
- key_points MUST be an array of 3 short bullet points
- Use double quotes for all strings
- No trailing commas
- Output the JSON object and nothing else"""

QUIZ_PROMPT = """You are a Kerala PSC exam question setter.

Based ONLY on the following news summaries, generate exactly 5 MCQ questions.

News summaries:
{summaries}

Rules:
- Each question must have exactly 4 options labeled "A. ...", "B. ...", "C. ...", "D. ..."
- Exactly 1 correct answer per question (must match one option exactly)
- No ambiguous or trick questions
- Moderate difficulty — suitable for a PSC prelims exam
- Base questions ONLY on the provided summaries, not general knowledge
- Each question must test a distinct fact from a different article
- Use double quotes for all strings. No trailing commas.

Output ONLY a JSON array. No markdown. No code blocks. No backticks. No explanation.
[
  {{
    "question": "...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_answer": "A. ...",
    "explanation": "one sentence explanation"
  }}
]"""


def build_article_prompt(article_text: str) -> str:
    return SYSTEM_PROMPT.format(article_text=article_text)


def build_quiz_prompt(summaries: str) -> str:
    return QUIZ_PROMPT.format(summaries=summaries)
