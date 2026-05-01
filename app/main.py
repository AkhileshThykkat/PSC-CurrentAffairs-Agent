from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import logger
from app.db.session import init_db
from app.api.routes.news import router as news_router
from app.api.routes.quiz import router as quiz_router

import app.models.raw_article
import app.models.processed_article
import app.models.quiz


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PSC Current Affairs Agent")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


settings = get_settings()

app = FastAPI(
    title="PSC Current Affairs Agent",
    description="AI-powered current affairs system for Kerala PSC exam preparation",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(news_router)
app.include_router(quiz_router)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/")
async def serve_home():
    return FileResponse("frontend/index.html")


@app.get("/quiz")
async def serve_quiz():
    return FileResponse("frontend/quiz.html")


@app.get("/archive")
async def serve_archive():
    return FileResponse("frontend/archive.html")
