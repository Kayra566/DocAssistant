from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "docassistant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "billing-reconcile-daily": {
            "task": "billing.reconcile",
            "schedule": 24 * 60 * 60,
        }
    },
)


@celery_app.task(name="ping")
def ping() -> str:
    """Sanity-check task."""
    return "pong"
