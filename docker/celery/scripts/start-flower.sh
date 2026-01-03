#!/bin/bash
# Celery Flower monitoring startup script for Legal AI System
# Web-based monitoring and administration tool for Celery

set -euo pipefail

# Configuration
FLOWER_PORT=${FLOWER_PORT:-5555}
FLOWER_BASIC_AUTH=${FLOWER_BASIC_AUTH:-admin:changeme123}
LOG_LEVEL=${CELERY_LOG_LEVEL:-info}
FLOWER_URL_PREFIX=${FLOWER_URL_PREFIX:-/flower}

echo "Starting Celery Flower monitoring..."
echo "Configuration:"
echo "  Port: ${FLOWER_PORT}"
echo "  URL Prefix: ${FLOWER_URL_PREFIX}"
echo "  Log Level: ${LOG_LEVEL}"

# Wait for Redis to be available
echo "Waiting for Redis to be available..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo "Redis is available"

# Wait for at least one worker to be available
echo "Waiting for Celery workers to be available..."
worker_count=0
while [ $worker_count -eq 0 ]; do
    worker_count=$(celery -A celery_app inspect active --json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")
    if [ "$worker_count" -eq 0 ]; then
        echo "No workers available - sleeping"
        sleep 5
    fi
done
echo "Celery workers are available"

echo "Starting Flower web interface..."

# Start Flower with configuration
exec celery -A celery_app flower \
    --port=${FLOWER_PORT} \
    --basic_auth=${FLOWER_BASIC_AUTH} \
    --url_prefix=${FLOWER_URL_PREFIX} \
    --logging=${LOG_LEVEL} \
    --persistent=true \
    --db=/tmp/flower.db \
    --max_tasks=10000 \
    --auto_refresh=true