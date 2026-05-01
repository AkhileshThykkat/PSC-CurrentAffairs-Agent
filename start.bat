@echo off
echo ============================================
echo   PSC Current Affairs Agent
echo ============================================
echo.
echo Starting services in separate windows...
echo.

start "PSC Agent - API Server" cmd /k "uv run uvicorn app.main:app --reload --port 8000"
start "PSC Agent - Celery Worker" cmd /k "uv run celery -A app.workers.celery_app worker --loglevel=info"
start "PSC Agent - Celery Beat" cmd /k "uv run celery -A app.workers.celery_app beat --loglevel=info"

echo.
echo Three windows opened. Services are starting...
echo App will be available at: http://localhost:8000
echo.
echo To trigger a scrape now: uv run python scripts/run_pipeline.py
echo.
pause
