#!/bin/bash
# Celery beat (scheduler) startup script for Legal AI System
# Manages periodic tasks like backups, reports, and maintenance

set -euo pipefail

LOG_LEVEL=${CELERY_LOG_LEVEL:-info}
SCHEDULE_FILE=${CELERY_SCHEDULE_FILE:-/tmp/celerybeat-schedule}

echo "Starting Celery Beat scheduler..."
echo "Configuration:"
echo "  Log Level: ${LOG_LEVEL}"
echo "  Schedule File: ${SCHEDULE_FILE}"

# Wait for Redis to be available
echo "Waiting for Redis to be available..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo "Redis is available"

# Ensure schedule file directory exists and is writable
mkdir -p "$(dirname "${SCHEDULE_FILE}")"
chown celeryuser:celeryuser "$(dirname "${SCHEDULE_FILE}")"

# Remove existing schedule file to start fresh
rm -f "${SCHEDULE_FILE}"

echo "Starting Celery Beat..."

# Start Celery Beat
exec celery -A celery_app beat \
    --loglevel=${LOG_LEVEL} \
    --schedule="${SCHEDULE_FILE}" \
    --pidfile=/tmp/celerybeat.pid \
    --logfile=/var/log/celery/beat.log