#!/bin/bash
# MinIO bucket setup script for Legal AI System
# Creates buckets and applies policies

set -euo pipefail

# Configuration
MINIO_ENDPOINT=${MINIO_ENDPOINT:-http://localhost:9000}
MINIO_ACCESS_KEY=${MINIO_ROOT_USER:-legalai_admin}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD:-changeme123456}

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
until curl -f "${MINIO_ENDPOINT}/minio/health/live" > /dev/null 2>&1; do
    echo "MinIO not ready, waiting..."
    sleep 5
done

echo "MinIO is ready, configuring..."

# Configure mc client
mc alias set minio "${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}"

# Create buckets for Legal AI System
BUCKETS=(
    "legal-documents:Legal document storage with versioning"
    "legal-contracts:Contract files and templates"
    "legal-case-files:Case-related documents and evidence"
    "legal-templates:Document templates and forms"
    "legal-backups:System backups and exports"
    "legal-reports:Generated reports and analytics"
    "legal-temp:Temporary file processing"
)

echo "Creating buckets..."
for bucket_info in "${BUCKETS[@]}"; do
    IFS=':' read -r bucket_name bucket_desc <<< "$bucket_info"
    
    if mc ls "minio/${bucket_name}" > /dev/null 2>&1; then
        echo "Bucket '${bucket_name}' already exists"
    else
        mc mb "minio/${bucket_name}"
        echo "Created bucket: ${bucket_name} - ${bucket_desc}"
    fi
    
    # Enable versioning for document buckets
    if [[ "${bucket_name}" =~ ^legal-(documents|contracts|case-files)$ ]]; then
        mc version enable "minio/${bucket_name}"
        echo "Enabled versioning for: ${bucket_name}"
    fi
done

# Set bucket policies
echo "Applying bucket policies..."
for policy_file in /etc/minio/policies/*.json; do
    if [[ -f "$policy_file" ]]; then
        policy_name=$(basename "$policy_file" .json)
        mc admin policy add minio "${policy_name}" "$policy_file"
        echo "Added policy: ${policy_name}"
    fi
done

# Create service account for Legal AI System
echo "Creating service account..."
SERVICE_ACCOUNT_KEY=$(mc admin user svcacct add minio legalai-admin --access-key "legalai-service" --secret-key "legalai-service-secret-key" 2>/dev/null || echo "exists")

if [[ "$SERVICE_ACCOUNT_KEY" != "exists" ]]; then
    echo "Service account created: legalai-service"
else
    echo "Service account already exists: legalai-service"
fi

# Set lifecycle policies for temporary files
echo "Setting lifecycle policies..."
cat > /tmp/lifecycle-temp.json << EOF
{
    "Rules": [
        {
            "ID": "TempFileCleanup",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "temp/"
            },
            "Expiration": {
                "Days": 7
            }
        },
        {
            "ID": "IncompleteMultipartCleanup",
            "Status": "Enabled",
            "AbortIncompleteMultipartUpload": {
                "DaysAfterInitiation": 1
            }
        }
    ]
}
EOF

mc ilm set minio/legal-temp < /tmp/lifecycle-temp.json
echo "Lifecycle policy applied to legal-temp bucket"

# Configure event notifications (webhook example)
echo "Configuring event notifications..."
# mc event add minio/legal-documents arn:minio:sqs::_:webhook --event put,delete

echo "MinIO bucket setup completed successfully"

# Display bucket information
echo ""
echo "Created buckets:"
mc ls minio/