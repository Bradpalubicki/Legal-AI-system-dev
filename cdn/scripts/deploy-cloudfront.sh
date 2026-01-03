#!/bin/bash
# =============================================================================
# CloudFront CDN Deployment Script
# Legal AI System - Production CDN Setup
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CDN_DIR="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$CDN_DIR/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi

    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed. Please install it first."
        exit 1
    fi

    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed. Some features may not work."
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials are not configured. Please run 'aws configure'."
        exit 1
    fi

    log_success "All prerequisites met"
}

validate_environment() {
    local env=$1

    if [[ ! "$env" =~ ^(development|staging|production)$ ]]; then
        log_error "Invalid environment: $env. Must be development, staging, or production."
        exit 1
    fi

    log_info "Environment: $env"
}

create_s3_backend() {
    log_info "Setting up Terraform S3 backend..."

    local bucket_name="legal-ai-terraform-state"
    local region="us-east-1"
    local table_name="legal-ai-terraform-locks"

    # Create S3 bucket if it doesn't exist
    if ! aws s3 ls "s3://$bucket_name" 2>/dev/null; then
        log_info "Creating S3 bucket: $bucket_name"
        aws s3api create-bucket \
            --bucket "$bucket_name" \
            --region "$region"

        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "$bucket_name" \
            --versioning-configuration Status=Enabled

        # Enable encryption
        aws s3api put-bucket-encryption \
            --bucket "$bucket_name" \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }'

        log_success "S3 backend bucket created"
    else
        log_info "S3 backend bucket already exists"
    fi

    # Create DynamoDB table if it doesn't exist
    if ! aws dynamodb describe-table --table-name "$table_name" 2>/dev/null; then
        log_info "Creating DynamoDB table: $table_name"
        aws dynamodb create-table \
            --table-name "$table_name" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region "$region"

        log_success "DynamoDB lock table created"
    else
        log_info "DynamoDB lock table already exists"
    fi
}

deploy_cloudfront_functions() {
    log_info "Deploying CloudFront Functions..."

    local functions_dir="$CDN_DIR/cloudfront/functions"

    # Deploy security headers function
    if [ -f "$functions_dir/security-headers.js" ]; then
        log_info "Deploying security-headers function..."

        # Check if function exists
        local function_name="legal-ai-security-headers"
        if aws cloudfront describe-function --name "$function_name" 2>/dev/null; then
            # Update existing function
            local etag=$(aws cloudfront describe-function --name "$function_name" --query 'ETag' --output text)
            aws cloudfront update-function \
                --name "$function_name" \
                --function-code "fileb://$functions_dir/security-headers.js" \
                --function-config '{"Comment":"Add security headers","Runtime":"cloudfront-js-1.0"}' \
                --if-match "$etag"

            log_success "Security headers function updated"
        else
            # Create new function
            aws cloudfront create-function \
                --name "$function_name" \
                --function-code "fileb://$functions_dir/security-headers.js" \
                --function-config '{"Comment":"Add security headers","Runtime":"cloudfront-js-1.0"}'

            log_success "Security headers function created"
        fi

        # Publish function
        local etag=$(aws cloudfront describe-function --name "$function_name" --query 'ETag' --output text)
        aws cloudfront publish-function --name "$function_name" --if-match "$etag"
        log_success "Security headers function published"
    fi

    # Deploy cache key normalization function
    if [ -f "$functions_dir/cache-key-normalization.js" ]; then
        log_info "Deploying cache-key-normalization function..."

        local function_name="legal-ai-cache-key-normalization"
        if aws cloudfront describe-function --name "$function_name" 2>/dev/null; then
            local etag=$(aws cloudfront describe-function --name "$function_name" --query 'ETag' --output text)
            aws cloudfront update-function \
                --name "$function_name" \
                --function-code "fileb://$functions_dir/cache-key-normalization.js" \
                --function-config '{"Comment":"Normalize cache keys","Runtime":"cloudfront-js-1.0"}' \
                --if-match "$etag"

            log_success "Cache key normalization function updated"
        else
            aws cloudfront create-function \
                --name "$function_name" \
                --function-code "fileb://$functions_dir/cache-key-normalization.js" \
                --function-config '{"Comment":"Normalize cache keys","Runtime":"cloudfront-js-1.0"}'

            log_success "Cache key normalization function created"
        fi

        local etag=$(aws cloudfront describe-function --name "$function_name" --query 'ETag' --output text)
        aws cloudfront publish-function --name "$function_name" --if-match "$etag"
        log_success "Cache key normalization function published"
    fi
}

terraform_deploy() {
    local environment=$1

    log_info "Deploying CDN infrastructure with Terraform..."

    cd "$TERRAFORM_DIR"

    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init

    # Validate configuration
    log_info "Validating Terraform configuration..."
    terraform validate

    # Plan deployment
    log_info "Planning Terraform deployment..."
    terraform plan \
        -var="environment=$environment" \
        -out=tfplan

    # Ask for confirmation
    echo
    read -p "Do you want to apply this plan? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log_warning "Deployment cancelled"
        rm -f tfplan
        exit 0
    fi

    # Apply deployment
    log_info "Applying Terraform configuration..."
    terraform apply tfplan
    rm -f tfplan

    log_success "CDN infrastructure deployed successfully"

    # Get outputs
    log_info "Deployment outputs:"
    terraform output
}

invalidate_cache() {
    log_info "Creating CloudFront invalidation..."

    # Get distribution ID from Terraform output
    cd "$TERRAFORM_DIR"
    local distribution_id=$(terraform output -raw cloudfront_distribution_id 2>/dev/null)

    if [ -z "$distribution_id" ]; then
        log_error "Could not get CloudFront distribution ID from Terraform output"
        return 1
    fi

    # Create invalidation
    local invalidation_id=$(aws cloudfront create-invalidation \
        --distribution-id "$distribution_id" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)

    log_success "Cache invalidation created: $invalidation_id"
    log_info "Waiting for invalidation to complete (this may take a few minutes)..."

    # Wait for invalidation to complete
    aws cloudfront wait invalidation-completed \
        --distribution-id "$distribution_id" \
        --id "$invalidation_id"

    log_success "Cache invalidation completed"
}

upload_static_assets() {
    log_info "Uploading static assets to S3..."

    cd "$TERRAFORM_DIR"
    local bucket_name=$(terraform output -raw static_assets_bucket 2>/dev/null)

    if [ -z "$bucket_name" ]; then
        log_error "Could not get S3 bucket name from Terraform output"
        return 1
    fi

    # Check if static assets directory exists
    local static_dir="$CDN_DIR/../frontend/public"
    if [ ! -d "$static_dir" ]; then
        log_warning "Static assets directory not found: $static_dir"
        return 0
    fi

    log_info "Syncing static assets to s3://$bucket_name/"
    aws s3 sync "$static_dir" "s3://$bucket_name/" \
        --delete \
        --cache-control "public, max-age=31536000, immutable" \
        --exclude "*.html" \
        --exclude "*.txt"

    # Upload HTML files with shorter cache
    aws s3 sync "$static_dir" "s3://$bucket_name/" \
        --cache-control "public, max-age=3600, must-revalidate" \
        --exclude "*" \
        --include "*.html"

    log_success "Static assets uploaded"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    local command=${1:-deploy}
    local environment=${2:-production}

    echo
    echo "========================================="
    echo "  CloudFront CDN Deployment"
    echo "  Legal AI System"
    echo "========================================="
    echo

    case "$command" in
        deploy)
            check_prerequisites
            validate_environment "$environment"
            create_s3_backend
            deploy_cloudfront_functions
            terraform_deploy "$environment"
            upload_static_assets
            log_success "CDN deployment completed successfully!"
            ;;

        invalidate)
            check_prerequisites
            invalidate_cache
            ;;

        upload)
            check_prerequisites
            upload_static_assets
            invalidate_cache
            ;;

        destroy)
            check_prerequisites
            validate_environment "$environment"

            echo
            log_warning "WARNING: This will destroy the CDN infrastructure!"
            read -p "Are you sure? Type 'yes' to confirm: " confirm
            if [ "$confirm" != "yes" ]; then
                log_info "Destroy cancelled"
                exit 0
            fi

            cd "$TERRAFORM_DIR"
            terraform destroy -var="environment=$environment"
            log_success "CDN infrastructure destroyed"
            ;;

        *)
            echo "Usage: $0 {deploy|invalidate|upload|destroy} [environment]"
            echo
            echo "Commands:"
            echo "  deploy      - Deploy full CDN infrastructure (default)"
            echo "  invalidate  - Invalidate CloudFront cache"
            echo "  upload      - Upload static assets and invalidate cache"
            echo "  destroy     - Destroy CDN infrastructure"
            echo
            echo "Environments: development, staging, production (default: production)"
            exit 1
            ;;
    esac

    echo
    log_success "All operations completed successfully!"
}

main "$@"
