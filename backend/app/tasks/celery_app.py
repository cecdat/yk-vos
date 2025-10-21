from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
celery = Celery('vos_tasks', broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery.conf.task_routes = {'app.tasks.sync_tasks.*': {'queue': 'sync'}}
celery.conf.timezone = 'Asia/Shanghai'
celery.conf.beat_schedule = {
    'sync-phones-every-5min': {'task': 'app.tasks.sync_tasks.sync_all_instances_online_phones','schedule': 300.0},
    'sync-cdr-daily-0130': {'task': 'app.tasks.sync_tasks.sync_all_instances_cdrs','schedule': crontab(minute=30, hour=1)},
}
