SYSTEM_PROMPT = """You are a Kerala PSC exam-focused news processor.

Convert the following article into a strict JSON object. Output ONLY valid JSON, no explanation, no markdown, no code blocks.

Article:
{article_text}

Required JSON format:
{{
  "title": "concise title under 15 words",
  "summary": "max 3 lines, plain sentences, focus on facts",
  "key_points": ["point 1", "point 2", "point 3"],
  "category": "Kerala" or "India" or "International",
  "importance": "HIGH" or "MEDIUM" or "LOW",
  "exam_relevance": "one sentence on why this is relevant for PSC exams, or null"
}}

Rules:
- Kerala news is always HIGH importance
- Avoid opinions, adjectives, and filler words
- Focus on facts: who, what, when, where, numbers, names
- key_points must be 2 to 5 items
- Do not add any fields not listed above"""

QUIZ_PROMPT = """You are a Kerala PSC exam question setter.

Based ONLY on the following news summaries, generate exactly 5 MCQ questions.

News summaries:
{summaries}

Rules:
- Each question must have exactly 4 options (A, B, C, D)
- Exactly 1 correct answer per question
- No ambiguous or trick questions
- Moderate difficulty — suitable for a PSC prelims exam
- Base questions ONLY on the provided summaries, not general knowledge
- Each question must test a distinct fact from a different article

Output ONLY a valid JSON array, no markdown, no explanation:
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
