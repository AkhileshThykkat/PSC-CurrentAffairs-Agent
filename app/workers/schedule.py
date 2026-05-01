from celery.schedules import crontab
from app.workers.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "scrape-every-3-hours": {
        "task": "app.workers.tasks.run_full_pipeline",
        "schedule": crontab(minute=0, hour="*/3"),
    },
    "daily-quiz-6am": {
        "task": "app.workers.tasks.generate_daily_quiz_task",
        "schedule": crontab(hour=6, minute=0),
    },
}
