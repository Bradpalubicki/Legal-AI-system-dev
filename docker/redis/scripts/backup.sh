#!/bin/bash
# Redis backup script for Legal AI System
# Creates snapshots with retention policy

set -euo pipefail

# Configuration
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}
REDIS_PASSWORD=${REDIS_PASSWORD:-changeme123}
BACKUP_DIR=${BACKUP_DIR:-/data/backups}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/redis_backup_${TIMESTAMP}.rdb"

echo "Starting Redis backup at $(date)"

# Trigger BGSAVE
if redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" BGSAVE; then
    echo "Background save initiated"
    
    # Wait for BGSAVE to complete
    while [[ $(redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" LASTSAVE) == $(redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" -a "${REDIS_PASSWORD}" LASTSAVE) ]]; do
        sleep 1
    done
    
    # Copy the RDB file
    cp /data/dump.rdb "${BACKUP_FILE}"
    gzip "${BACKUP_FILE}"
    
    echo "Backup created: ${BACKUP_FILE}.gz"
    
    # Clean up old backups
    find "${BACKUP_DIR}" -name "redis_backup_*.rdb.gz" -mtime +${RETENTION_DAYS} -delete
    echo "Old backups cleaned up (retention: ${RETENTION_DAYS} days)"
    
else
    echo "ERROR: Redis backup failed" >&2
    exit 1
fi

echo "Redis backup completed at $(date)"