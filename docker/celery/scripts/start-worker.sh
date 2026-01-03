#!/bin/bash
# Celery worker startup script for Legal AI System
# Supports different worker types and configurations

set -euo pipefail

# Default configuration
WORKER_TYPE=${CELERY_WORKER_TYPE:-general}
CONCURRENCY=${CELERY_CONCURRENCY:-4}
LOG_LEVEL=${CELERY_LOG_LEVEL:-info}
QUEUES=${CELERY_QUEUES:-default}
MAX_TASKS_PER_CHILD=${CELERY_MAX_TASKS_PER_CHILD:-1000}
MAX_MEMORY_PER_CHILD=${CELERY_MAX_MEMORY_PER_CHILD:-200000}

echo "Starting Celery worker: ${WORKER_TYPE}"
echo "Configuration:"
echo "  Concurrency: ${CONCURRENCY}"
echo "  Log Level: ${LOG_LEVEL}"
echo "  Queues: ${QUEUES}"
echo "  Max Tasks Per Child: ${MAX_TASKS_PER_CHILD}"
echo "  Max Memory Per Child: ${MAX_MEMORY_PER_CHILD}KB"

# Wait for Redis to be available
echo "Waiting for Redis to be available..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo "Redis is available"

# Configure worker based on type
case ${WORKER_TYPE} in
    "document")
        echo "Starting document processing worker..."
        QUEUES="document_processing"
        CONCURRENCY=2
        MAX_MEMORY_PER_CHILD=500000  # 500MB for document processing
        ;;
    "ai")
        echo "Starting AI analysis worker..."
        QUEUES="ai_analysis"
        CONCURRENCY=1  # AI tasks are memory intensive
        MAX_MEMORY_PER_CHILD=1000000  # 1GB for AI processing
        ;;
    "email")
        echo "Starting email processing worker..."
        QUEUES="email_processing"
        CONCURRENCY=8
        ;;
    "reports")
        echo "Starting report generation worker..."
        QUEUES="report_generation"
        CONCURRENCY=2
        MAX_MEMORY_PER_CHILD=300000  # 300MB for report generation
        ;;
    "billing")
        echo "Starting billing worker..."
        QUEUES="billing"
        CONCURRENCY=4
        ;;
    "maintenance")
        echo "Starting maintenance worker..."
        QUEUES="maintenance"
        CONCURRENCY=1
        ;;
    "general"|*)
        echo "Starting general purpose worker..."
        QUEUES="default,document_processing,email_processing,billing"
        ;;
esac

# Export environment variables for Celery
export CELERY_WORKER_TYPE
export CELERY_CONCURRENCY=${CONCURRENCY}
export CELERY_LOG_LEVEL=${LOG_LEVEL}

# Start Celery worker with configuration
exec celery -A celery_app worker \
    --loglevel=${LOG_LEVEL} \
    --concurrency=${CONCURRENCY} \
    --queues=${QUEUES} \
    --hostname=${WORKER_TYPE}@%h \
    --max-tasks-per-child=${MAX_TASKS_PER_CHILD} \
    --max-memory-per-child=${MAX_MEMORY_PER_CHILD} \
    --time-limit=3600 \
    --soft-time-limit=1800 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat \
    --logfile=/var/log/celery/${WORKER_TYPE}_worker.log