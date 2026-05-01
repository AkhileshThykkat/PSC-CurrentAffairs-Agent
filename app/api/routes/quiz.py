import json
import logging
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.api.deps import get_db
from app.models.quiz import Quiz
from app.schemas.quiz import QuizQuestionResponse, QuizResponse

logger = logging.getLogger("psc_agent.api.quiz")

router = APIRouter(prefix="/quiz", tags=["quiz"])


def quiz_to_response(q: Quiz) -> QuizQuestionResponse:
    return QuizQuestionResponse(
        id=q.id,
        question=q.question,
        options=json.loads(q.options),
        correct_answer=q.correct_answer,
        explanation=q.explanation,
    )


@router.get("/today", response_model=QuizResponse)
def get_today_quiz(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.date == today)
        .order_by(Quiz.id)
        .all()
    )
    if not quizzes:
        raise HTTPException(status_code=404, detail="No quiz available for today")
    return QuizResponse(
        date=today.isoformat(),
        questions=[quiz_to_response(q) for q in quizzes],
    )


@router.get("", response_model=QuizResponse)
def get_quiz(
    days: int = Query(default=1, ge=1, le=365),
    db: Session = Depends(get_db),
):
    cutoff = datetime.utcnow().date() - timedelta(days=days - 1)
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.date >= cutoff)
        .order_by(desc(Quiz.date), Quiz.id)
        .all()
    )
    if not quizzes:
        raise HTTPException(status_code=404, detail="No quizzes found for the given period")

    questions = [quiz_to_response(q) for q in quizzes]
    return QuizResponse(
        date=quizzes[0].date.isoformat() if quizzes else "",
        questions=questions,
    )


@router.get("/{quiz_date}", response_model=QuizResponse)
def get_quiz_by_date(quiz_date: str, db: Session = Depends(get_db)):
    try:
        target_date = date.fromisoformat(quiz_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD")

    quizzes = (
        db.query(Quiz)
        .filter(Quiz.date == target_date)
        .order_by(Quiz.id)
        .all()
    )
    if not quizzes:
        raise HTTPException(status_code=404, detail=f"No quiz found for {quiz_date}")

    return QuizResponse(
        date=target_date.isoformat(),
        questions=[quiz_to_response(q) for q in quizzes],
    )
