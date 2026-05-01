from datetime import date, datetime
from pydantic import BaseModel


class QuizQuestionResponse(BaseModel):
    id: int
    question: str
    options: list[str]
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    date: str
    questions: list[QuizQuestionResponse]
