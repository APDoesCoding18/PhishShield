from celery import Celery
from app.core.config import settings

# Initialize Celery infrastructure
broker_url = "memory://" if settings.CELERY_TASK_ALWAYS_EAGER else settings.REDIS_URL
backend_url = "cache+memory://" if settings.CELERY_TASK_ALWAYS_EAGER else settings.REDIS_URL

celery_app = Celery(
    "phishshield_worker",
    broker=broker_url,
    backend=backend_url,
)

# Configuration for Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
)
