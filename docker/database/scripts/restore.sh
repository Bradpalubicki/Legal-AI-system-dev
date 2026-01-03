#!/bin/bash
# Database restore script for Legal AI System
# Restores from encrypted backups with safety checks

set -euo pipefail

# Configuration
DB_NAME=${POSTGRES_DB:-legalai_db}
DB_USER=${POSTGRES_USER:-legalai_user}
BACKUP_DIR=${BACKUP_DIR:-/var/lib/postgresql/backups}
ENCRYPTION_KEY=${BACKUP_ENCRYPTION_KEY:-}

# Function to show usage
show_usage() {
    echo "Usage: $0 <backup_file>"
    echo "  backup_file: Path to backup file or just the filename (will search in ${BACKUP_DIR})"
    echo ""
    echo "Examples:"
    echo "  $0 legalai_backup_20241201_120000.sql.gz"
    echo "  $0 /path/to/backup.sql.gz.gpg"
}

# Check arguments
if [[ $# -ne 1 ]]; then
    show_usage
    exit 1
fi

BACKUP_FILE_INPUT="$1"

# Determine full path to backup file
if [[ -f "${BACKUP_FILE_INPUT}" ]]; then
    BACKUP_FILE="${BACKUP_FILE_INPUT}"
elif [[ -f "${BACKUP_DIR}/${BACKUP_FILE_INPUT}" ]]; then
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILE_INPUT}"
else
    echo "ERROR: Backup file not found: ${BACKUP_FILE_INPUT}" >&2
    exit 1
fi

echo "Legal AI System Database Restore"
echo "================================"
echo "Database: ${DB_NAME}"
echo "Backup file: ${BACKUP_FILE}"
echo "Restore time: $(date)"
echo ""

# Safety confirmation
read -p "WARNING: This will completely replace the existing database. Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Prepare restore file
RESTORE_FILE="/tmp/restore_$(date +%s).sql"

# Handle encrypted files
if [[ "${BACKUP_FILE}" == *.gpg ]]; then
    if [[ -z "${ENCRYPTION_KEY}" ]]; then
        echo "ERROR: Backup is encrypted but no encryption key provided" >&2
        echo "Set BACKUP_ENCRYPTION_KEY environment variable" >&2
        exit 1
    fi
    
    echo "Decrypting backup file..."
    gpg --decrypt --quiet --batch --yes \
        --passphrase "${ENCRYPTION_KEY}" \
        "${BACKUP_FILE}" > "${RESTORE_FILE}.gz"
    
    echo "Decompressing backup file..."
    gunzip "${RESTORE_FILE}.gz"
    
elif [[ "${BACKUP_FILE}" == *.gz ]]; then
    echo "Decompressing backup file..."
    gunzip -c "${BACKUP_FILE}" > "${RESTORE_FILE}"
else
    echo "Copying backup file..."
    cp "${BACKUP_FILE}" "${RESTORE_FILE}"
fi

# Verify backup file
if [[ ! -s "${RESTORE_FILE}" ]]; then
    echo "ERROR: Restore file is empty or corrupted" >&2
    rm -f "${RESTORE_FILE}"
    exit 1
fi

echo "Backup file prepared successfully"

# Create backup of current database
echo "Creating backup of current database..."
CURRENT_BACKUP="${BACKUP_DIR}/pre_restore_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
mkdir -p "${BACKUP_DIR}"

if pg_dump -h localhost -U "${DB_USER}" -d "${DB_NAME}" \
    --format=custom --no-owner --no-privileges | gzip > "${CURRENT_BACKUP}"; then
    echo "Current database backed up to: ${CURRENT_BACKUP}"
else
    echo "WARNING: Failed to backup current database" >&2
fi

# Drop existing connections
echo "Terminating existing database connections..."
psql -h localhost -U postgres -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
    2>/dev/null || true

# Restore database
echo "Restoring database from backup..."
if psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" < "${RESTORE_FILE}"; then
    echo "Database restore completed successfully"
    
    # Verify restore
    echo "Verifying database restore..."
    TABLE_COUNT=$(psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'legalai';" | tr -d ' ')
    
    if [[ "${TABLE_COUNT}" -gt 0 ]]; then
        echo "Verification successful: ${TABLE_COUNT} tables found in legalai schema"
    else
        echo "WARNING: Verification failed - no tables found in legalai schema" >&2
    fi
    
    # Update statistics
    echo "Updating database statistics..."
    psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -c "ANALYZE;" > /dev/null
    
else
    echo "ERROR: Database restore failed" >&2
    echo "Current database backup available at: ${CURRENT_BACKUP}" >&2
    rm -f "${RESTORE_FILE}"
    exit 1
fi

# Cleanup
rm -f "${RESTORE_FILE}"

echo ""
echo "Restore process completed successfully at $(date)"
echo "Previous database backup saved as: ${CURRENT_BACKUP}"
echo ""
echo "IMPORTANT: Please verify your application connectivity and data integrity."