from celery import Celery
from kombu import Exchange, Queue
from typing import Any
import os

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery instance
celery_app = Celery(
    "app",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

# Celery configuration
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
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

# Define queues
default_exchange = Exchange("default", type="direct")
high_priority_exchange = Exchange("high_priority", type="direct")
low_priority_exchange = Exchange("low_priority", type="direct")

celery_app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("high_priority", high_priority_exchange, routing_key="high_priority"),
    Queue("low_priority", low_priority_exchange, routing_key="low_priority"),
)

# Route tasks to appropriate queues
celery_app.conf.task_routes = {
    "app.tasks.process_high_priority_task": {"queue": "high_priority"},
    "app.tasks.process_low_priority_task": {"queue": "low_priority"},
    "app.tasks.send_email": {"queue": "default"},
    "app.tasks.generate_report": {"queue": "low_priority"},
}

# Task annotations for better performance
celery_app.conf.task_annotations = {
    "*": {"rate_limit": "10/s"},
    "app.tasks.send_email": {"rate_limit": "5/m"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-expired-data": {
        "task": "app.tasks.cleanup_expired_data",
        "schedule": 3600.0,  # Every hour
    },
    "generate-daily-report": {
        "task": "app.tasks.generate_daily_report",
        "schedule": 86400.0,  # Every day
    },
}

if __name__ == "__main__":
    celery_app.start()