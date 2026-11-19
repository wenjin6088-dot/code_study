import os

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("code_study", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_routes={
        "src.tasks.document_generation.*": {"queue": "document_generation"},
        "src.tasks.practice_generation.*": {"queue": "practice_generation"},
        "src.tasks.trash_cleanup.*": {"queue": "cleanup"},
    },
    task_default_queue="default",
    task_time_limit=300,
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
