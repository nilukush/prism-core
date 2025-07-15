"""
Celery application configuration.
Handles background tasks and scheduled jobs.
"""

from celery import Celery
from celery.schedules import crontab

from backend.src.core.config import settings

# Create Celery app
celery_app = Celery(
    "prism",
    broker=str(settings.CELERY_BROKER_URL),
    backend=str(settings.CELERY_RESULT_BACKEND),
    include=[
        "backend.src.workers.tasks.story_tasks",
        "backend.src.workers.tasks.document_tasks",
        "backend.src.workers.tasks.sync_tasks",
        "backend.src.workers.tasks.analytics_tasks",
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "sync-integrations": {
        "task": "backend.src.workers.tasks.sync_tasks.sync_all_integrations",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    "cleanup-old-sessions": {
        "task": "backend.src.workers.tasks.cleanup_tasks.cleanup_old_sessions",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "generate-analytics-report": {
        "task": "backend.src.workers.tasks.analytics_tasks.generate_daily_report",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
    },
    "cleanup-vector-store": {
        "task": "backend.src.workers.tasks.cleanup_tasks.cleanup_vector_store",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Weekly on Sunday at 3 AM
    },
}

if __name__ == "__main__":
    celery_app.start()