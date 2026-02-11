"""
Celery application configuration for the Energy Management SaaS platform.

Defines the Celery app instance, beat schedule for periodic tasks,
and serialization / result backend settings.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

# ---------------------------------------------------------------------------
# Settings import -- may not be available during Celery worker bootstrap
# (e.g. when env vars are missing), so we fall back to sensible defaults.
# ---------------------------------------------------------------------------
try:
    from app.config import settings

    BROKER_URL = settings.REDIS_URL
except Exception:
    BROKER_URL = "redis://redis:6379/0"

# ---------------------------------------------------------------------------
# Celery application
# ---------------------------------------------------------------------------
celery_app = Celery(
    "energy_management",
    broker=BROKER_URL,
    include=[
        "app.tasks.sync_data",
        "app.tasks.run_autopilot",
        "app.tasks.analytics",
    ],
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Result backend
    result_backend=BROKER_URL,
    result_expires=3600,  # 1 hour
    # Timezone
    timezone="Europe/Paris",
    enable_utc=True,
    # Beat schedule
    beat_schedule={
        "run_autopilot_cycle": {
            "task": "app.tasks.run_autopilot.run_autopilot_cycle",
            "schedule": crontab(minute="*/15"),  # every 15 minutes
        },
        "sync_energy_data": {
            "task": "app.tasks.sync_data.sync_energy_data",
            "schedule": crontab(hour=6, minute=0),  # daily at 06:00 UTC
        },
        "train_forecasting_models": {
            "task": "app.tasks.analytics.train_forecasting_models",
            "schedule": crontab(
                hour=2, minute=0, day_of_week="sunday",
            ),  # every Sunday at 02:00 UTC
        },
        "calculate_daily_analytics": {
            "task": "app.tasks.analytics.calculate_daily_analytics",
            "schedule": crontab(hour=0, minute=30),  # daily at 00:30 UTC
        },
    },
    # Misc
    task_track_started=True,
    worker_hijack_root_logger=False,
)
