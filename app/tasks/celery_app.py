from celery import Celery
from app.core.config import settings

broker = settings.CELERY_BROKER_URL or settings.REDIS_URL
backend = settings.CELERY_RESULT_BACKEND or settings.REDIS_URL

celery_app = Celery("mini_ecommerce", broker=broker, backend=backend)
celery_app.conf.update(
    task_always_eager=False,
    task_ignore_result=True,
)
