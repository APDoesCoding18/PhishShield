from celery import Celery
from app.core.config import settings

# Initialize Celery infrastructure
celery_app = Celery(
    "phishshield_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Optional: Configuration for Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
)
