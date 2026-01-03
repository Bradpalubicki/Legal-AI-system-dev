#!/bin/bash
# Database backup script for Legal AI System
# Performs encrypted backups with retention policy

set -euo pipefail

# Configuration
DB_NAME=${POSTGRES_DB:-legalai_db}
DB_USER=${POSTGRES_USER:-legalai_user}
BACKUP_DIR=${BACKUP_DIR:-/var/lib/postgresql/backups}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY:-}

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/legalai_backup_${TIMESTAMP}.sql"
COMPRESSED_FILE="${BACKUP_FILE}.gz"

echo "Starting backup of ${DB_NAME} at $(date)"

# Perform backup
if pg_dump -h localhost -U "${DB_USER}" -d "${DB_NAME}" \
    --verbose \
    --format=custom \
    --no-owner \
    --no-privileges \
    > "${BACKUP_FILE}"; then
    
    echo "Database backup completed successfully"
    
    # Compress backup
    gzip "${BACKUP_FILE}"
    echo "Backup compressed: ${COMPRESSED_FILE}"
    
    # Encrypt backup if key is provided
    if [[ -n "${ENCRYPTION_KEY}" ]]; then
        gpg --symmetric --cipher-algo AES256 --batch --yes \
            --passphrase "${ENCRYPTION_KEY}" \
            --output "${COMPRESSED_FILE}.gpg" \
            "${COMPRESSED_FILE}"
        
        # Remove unencrypted file
        rm "${COMPRESSED_FILE}"
        echo "Backup encrypted: ${COMPRESSED_FILE}.gpg"
    fi
    
    # Clean up old backups
    find "${BACKUP_DIR}" -name "legalai_backup_*.sql.gz*" -mtime +${RETENTION_DAYS} -delete
    echo "Old backups cleaned up (retention: ${RETENTION_DAYS} days)"
    
    # Log backup info
    BACKUP_SIZE=$(du -h "${COMPRESSED_FILE}${ENCRYPTION_KEY:+.gpg}" | cut -f1)
    echo "Backup completed successfully:"
    echo "  File: $(basename "${COMPRESSED_FILE}${ENCRYPTION_KEY:+.gpg}")"
    echo "  Size: ${BACKUP_SIZE}"
    echo "  Location: ${BACKUP_DIR}"
    
else
    echo "ERROR: Database backup failed" >&2
    exit 1
fi

echo "Backup process completed at $(date)"