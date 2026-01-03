"""
Celery Configuration

Background task queue for marketing automation:
- CourtListener polling
- Email queue processing
- Newsletter generation
- Analytics rollup
"""

import os
from celery import Celery
from celery.schedules import crontab

# Get Redis URL from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# Create Celery app
celery_app = Celery(
    "marketing_workers",
    broker=CELERY_BROKER,
    backend=CELERY_BACKEND,
    include=['app.marketing.workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone=os.getenv('CAMPAIGN_TIMEZONE', 'America/New_York'),
    enable_utc=True,

    # Task execution
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 minute soft limit

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for predictability
    worker_concurrency=int(os.getenv('CELERY_CONCURRENCY', '4')),

    # Result settings
    result_expires=86400,  # Results expire after 1 day

    # Rate limiting
    task_default_rate_limit='10/m',  # Default 10 tasks per minute
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Poll CourtListener for new filings every 30 minutes
    "poll-courtlistener": {
        "task": "app.marketing.workers.tasks.poll_courtlistener",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "courtlistener"}
    },

    # Process email queue every 5 minutes
    "process-email-queue": {
        "task": "app.marketing.workers.tasks.process_email_queue",
        "schedule": crontab(minute="*/5"),
        "options": {"queue": "email"}
    },

    # Generate weekly newsletter - Sunday 6pm ET
    "generate-weekly-newsletter": {
        "task": "app.marketing.workers.tasks.generate_weekly_newsletter",
        "schedule": crontab(day_of_week=0, hour=18, minute=0),
        "options": {"queue": "newsletter"}
    },

    # Send weekly newsletter - Monday 9am ET
    "send-weekly-newsletter": {
        "task": "app.marketing.workers.tasks.send_weekly_newsletter",
        "schedule": crontab(day_of_week=1, hour=9, minute=0),
        "options": {"queue": "newsletter"}
    },

    # Daily analytics rollup - midnight ET
    "daily-analytics-rollup": {
        "task": "app.marketing.workers.tasks.daily_analytics_rollup",
        "schedule": crontab(hour=0, minute=0),
        "options": {"queue": "analytics"}
    },

    # Update campaign metrics every hour
    "update-campaign-metrics": {
        "task": "app.marketing.workers.tasks.update_all_campaign_metrics",
        "schedule": crontab(minute=0),
        "options": {"queue": "analytics"}
    },

    # Process pending opt-outs every hour (CAN-SPAM compliance)
    "process-opt-outs": {
        "task": "app.marketing.workers.tasks.process_opt_outs",
        "schedule": crontab(minute=0),
        "options": {"queue": "compliance"}
    },

    # Retry failed case notification emails every 15 minutes
    "retry-failed-notification-emails": {
        "task": "app.marketing.workers.tasks.retry_failed_notification_emails",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "email"}
    },
}

# Task routing
celery_app.conf.task_routes = {
    "app.marketing.workers.tasks.poll_courtlistener": {"queue": "courtlistener"},
    "app.marketing.workers.tasks.process_email_queue": {"queue": "email"},
    "app.marketing.workers.tasks.send_campaign_email": {"queue": "email"},
    "app.marketing.workers.tasks.generate_weekly_newsletter": {"queue": "newsletter"},
    "app.marketing.workers.tasks.send_weekly_newsletter": {"queue": "newsletter"},
    "app.marketing.workers.tasks.daily_analytics_rollup": {"queue": "analytics"},
    "app.marketing.workers.tasks.update_all_campaign_metrics": {"queue": "analytics"},
    "app.marketing.workers.tasks.process_opt_outs": {"queue": "compliance"},
    # Case notification tasks
    "app.marketing.workers.tasks.send_case_notification_email": {"queue": "email"},
    "app.marketing.workers.tasks.retry_failed_notification_emails": {"queue": "email"},
}
