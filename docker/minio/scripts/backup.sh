#!/bin/bash
# MinIO backup script for Legal AI System
# Creates incremental backups of legal document storage

set -euo pipefail

# Configuration
MINIO_ENDPOINT=${MINIO_ENDPOINT:-http://localhost:9000}
MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-legalai_admin}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-changeme123456}
BACKUP_DIR=${BACKUP_DIR:-/data/backups}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Configure mc client
mc alias set minio "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Starting MinIO backup at $(date)"

# Buckets to backup
BUCKETS=("legal-documents" "legal-contracts" "legal-case-files" "legal-templates")

for bucket in "${BUCKETS[@]}"; do
    echo "Backing up bucket: ${bucket}"
    
    BUCKET_BACKUP_DIR="${BACKUP_DIR}/${bucket}_${TIMESTAMP}"
    mkdir -p "${BUCKET_BACKUP_DIR}"
    
    # Mirror bucket contents to backup directory
    if mc mirror "minio/${bucket}" "${BUCKET_BACKUP_DIR}" --overwrite; then
        echo "Successfully backed up ${bucket}"
        
        # Create compressed archive
        tar -czf "${BACKUP_DIR}/${bucket}_${TIMESTAMP}.tar.gz" -C "${BACKUP_DIR}" "${bucket}_${TIMESTAMP}"
        
        # Remove uncompressed backup
        rm -rf "${BUCKET_BACKUP_DIR}"
        
        echo "Compressed backup created: ${bucket}_${TIMESTAMP}.tar.gz"
    else
        echo "ERROR: Failed to backup ${bucket}" >&2
    fi
done

# Export bucket policies and configurations
echo "Exporting bucket configurations..."
CONFIG_BACKUP_DIR="${BACKUP_DIR}/config_${TIMESTAMP}"
mkdir -p "${CONFIG_BACKUP_DIR}"

# Export policies
mc admin policy list minio > "${CONFIG_BACKUP_DIR}/policies.txt"

# Export user accounts (metadata only, no secrets)
mc admin user list minio > "${CONFIG_BACKUP_DIR}/users.txt"

# Export bucket info
for bucket in "${BUCKETS[@]}"; do
    mc stat "minio/${bucket}" > "${CONFIG_BACKUP_DIR}/${bucket}_info.txt" 2>/dev/null || true
    mc version info "minio/${bucket}" > "${CONFIG_BACKUP_DIR}/${bucket}_versioning.txt" 2>/dev/null || true
    mc ilm ls "minio/${bucket}" > "${CONFIG_BACKUP_DIR}/${bucket}_lifecycle.txt" 2>/dev/null || true
done

# Compress configuration backup
tar -czf "${BACKUP_DIR}/minio_config_${TIMESTAMP}.tar.gz" -C "${BACKUP_DIR}" "config_${TIMESTAMP}"
rm -rf "${CONFIG_BACKUP_DIR}"

echo "Configuration backup created: minio_config_${TIMESTAMP}.tar.gz"

# Clean up old backups
echo "Cleaning up old backups (retention: ${RETENTION_DAYS} days)"
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete

# Generate backup report
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
BACKUP_COUNT=$(find "${BACKUP_DIR}" -name "*_${TIMESTAMP}.tar.gz" | wc -l)

echo ""
echo "Backup Summary:"
echo "  Timestamp: ${TIMESTAMP}"
echo "  Buckets backed up: ${#BUCKETS[@]}"
echo "  Files created: ${BACKUP_COUNT}"
echo "  Total backup size: ${TOTAL_SIZE}"
echo "  Retention period: ${RETENTION_DAYS} days"

echo "MinIO backup completed at $(date)"