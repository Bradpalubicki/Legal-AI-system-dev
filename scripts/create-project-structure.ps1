# =============================================================================
# LEGAL AI SYSTEM - PROJECT STRUCTURE CREATION SCRIPT
# =============================================================================
# PowerShell script to create complete directory structure for Legal AI System
# Includes backend, frontend, infrastructure, documentation, and tooling folders
# =============================================================================

param(
    [string]$ProjectPath = ".",
    [switch]$Verbose,
    [switch]$WhatIf
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Colors = @{
    Success = "Green"
    Info    = "Cyan"
    Warning = "Yellow"
    Error   = "Red"
    Header  = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function New-DirectoryStructure {
    param(
        [string]$Path,
        [string]$Description = ""
    )
    
    if ($WhatIf) {
        Write-ColorOutput "Would create: $Path" "Info"
        return
    }
    
    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        if ($Verbose) {
            $displayPath = $Path -replace [regex]::Escape($ProjectPath), "."
            Write-ColorOutput "Created: $displayPath" "Success"
            if ($Description) {
                Write-ColorOutput "  → $Description" "Info"
            }
        }
    } else {
        if ($Verbose) {
            $displayPath = $Path -replace [regex]::Escape($ProjectPath), "."
            Write-ColorOutput "Exists: $displayPath" "Warning"
        }
    }
}

function New-PlaceholderFile {
    param(
        [string]$Path,
        [string]$Content = ""
    )
    
    if ($WhatIf) {
        Write-ColorOutput "Would create file: $Path" "Info"
        return
    }
    
    if (!(Test-Path $Path)) {
        if ($Content) {
            Set-Content -Path $Path -Value $Content
        } else {
            New-Item -ItemType File -Path $Path -Force | Out-Null
        }
        if ($Verbose) {
            $displayPath = $Path -replace [regex]::Escape($ProjectPath), "."
            Write-ColorOutput "Created file: $displayPath" "Success"
        }
    }
}

# =============================================================================
# MAIN SCRIPT EXECUTION
# =============================================================================

Write-ColorOutput "`n=============================================================================`n" "Header"
Write-ColorOutput "LEGAL AI SYSTEM - PROJECT STRUCTURE CREATION" "Header"
Write-ColorOutput "`n=============================================================================`n" "Header"

# Resolve full project path
$ProjectPath = Resolve-Path $ProjectPath

Write-ColorOutput "Creating project structure in: $ProjectPath" "Info"
Write-ColorOutput "Verbose mode: $Verbose" "Info"
Write-ColorOutput "WhatIf mode: $WhatIf`n" "Info"

# =============================================================================
# ROOT LEVEL DIRECTORIES
# =============================================================================

Write-ColorOutput "Creating root-level directories..." "Header"

# Main source directories
New-DirectoryStructure "$ProjectPath\backend" "FastAPI Python backend application"
New-DirectoryStructure "$ProjectPath\frontend" "Next.js React frontend application"
New-DirectoryStructure "$ProjectPath\shared" "Shared utilities and types"
New-DirectoryStructure "$ProjectPath\mobile" "Mobile application (future)"

# Infrastructure and deployment
New-DirectoryStructure "$ProjectPath\docker" "Docker configuration files"
New-DirectoryStructure "$ProjectPath\kubernetes" "Kubernetes deployment manifests"
New-DirectoryStructure "$ProjectPath\terraform" "Infrastructure as Code"
New-DirectoryStructure "$ProjectPath\ansible" "Configuration management"

# Data and storage
New-DirectoryStructure "$ProjectPath\storage" "Local file storage"
New-DirectoryStructure "$ProjectPath\data" "Data files and datasets"
New-DirectoryStructure "$ProjectPath\backups" "Database and file backups"

# Configuration and secrets
New-DirectoryStructure "$ProjectPath\config" "Configuration files"
New-DirectoryStructure "$ProjectPath\secrets" "Secret management (excluded from git)"

# Scripts and tools
New-DirectoryStructure "$ProjectPath\scripts" "Automation and utility scripts"
New-DirectoryStructure "$ProjectPath\tools" "Development tools and utilities"

# Documentation
New-DirectoryStructure "$ProjectPath\docs" "Project documentation"
New-DirectoryStructure "$ProjectPath\examples" "Usage examples and samples"

# Testing and quality assurance
New-DirectoryStructure "$ProjectPath\tests" "Integration and E2E tests"
New-DirectoryStructure "$ProjectPath\load-tests" "Performance testing"

# Monitoring and observability
New-DirectoryStructure "$ProjectPath\monitoring" "Monitoring configuration"
New-DirectoryStructure "$ProjectPath\logs" "Application logs"

# CI/CD
New-DirectoryStructure "$ProjectPath\.github" "GitHub workflows and templates"
New-DirectoryStructure "$ProjectPath\ci" "CI/CD configuration"

# =============================================================================
# BACKEND DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating backend directory structure..." "Header"

# Main application
New-DirectoryStructure "$ProjectPath\backend\app" "Main FastAPI application"
New-DirectoryStructure "$ProjectPath\backend\app\api" "API route handlers"
New-DirectoryStructure "$ProjectPath\backend\app\api\v1" "API version 1 endpoints"
New-DirectoryStructure "$ProjectPath\backend\app\api\v1\endpoints" "Individual API endpoints"
New-DirectoryStructure "$ProjectPath\backend\app\api\deps" "API dependencies and utilities"

# Core application modules
New-DirectoryStructure "$ProjectPath\backend\app\core" "Core application configuration"
New-DirectoryStructure "$ProjectPath\backend\app\models" "Database models"
New-DirectoryStructure "$ProjectPath\backend\app\schemas" "Pydantic schemas"
New-DirectoryStructure "$ProjectPath\backend\app\services" "Business logic services"
New-DirectoryStructure "$ProjectPath\backend\app\utils" "Utility functions"
New-DirectoryStructure "$ProjectPath\backend\app\middleware" "Custom middleware"

# Database
New-DirectoryStructure "$ProjectPath\backend\app\db" "Database configuration"
New-DirectoryStructure "$ProjectPath\backend\alembic" "Database migrations"
New-DirectoryStructure "$ProjectPath\backend\alembic\versions" "Migration versions"

# AI and ML modules
New-DirectoryStructure "$ProjectPath\backend\app\ai" "AI/ML integration modules"
New-DirectoryStructure "$ProjectPath\backend\app\ai\models" "AI model configurations"
New-DirectoryStructure "$ProjectPath\backend\app\ai\prompts" "AI prompts and templates"
New-DirectoryStructure "$ProjectPath\backend\app\ai\processors" "Document processors"

# Legal-specific modules
New-DirectoryStructure "$ProjectPath\backend\app\legal" "Legal-specific functionality"
New-DirectoryStructure "$ProjectPath\backend\app\legal\citation" "Citation processing"
New-DirectoryStructure "$ProjectPath\backend\app\legal\research" "Legal research APIs"
New-DirectoryStructure "$ProjectPath\backend\app\legal\documents" "Document analysis"
New-DirectoryStructure "$ProjectPath\backend\app\legal\compliance" "Compliance and audit"

# Background tasks
New-DirectoryStructure "$ProjectPath\backend\app\tasks" "Celery background tasks"
New-DirectoryStructure "$ProjectPath\backend\app\workers" "Worker configurations"

# Testing
New-DirectoryStructure "$ProjectPath\backend\tests" "Backend tests"
New-DirectoryStructure "$ProjectPath\backend\tests\unit" "Unit tests"
New-DirectoryStructure "$ProjectPath\backend\tests\integration" "Integration tests"
New-DirectoryStructure "$ProjectPath\backend\tests\fixtures" "Test fixtures and data"

# Configuration and deployment
New-DirectoryStructure "$ProjectPath\backend\config" "Backend configuration files"
New-DirectoryStructure "$ProjectPath\backend\scripts" "Backend-specific scripts"
New-DirectoryStructure "$ProjectPath\backend\requirements" "Python requirements files"

# =============================================================================
# FRONTEND DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating frontend directory structure..." "Header"

# Next.js application structure
New-DirectoryStructure "$ProjectPath\frontend\src" "Source code"
New-DirectoryStructure "$ProjectPath\frontend\src\app" "Next.js App Router"
New-DirectoryStructure "$ProjectPath\frontend\src\app\(auth)" "Authentication routes"
New-DirectoryStructure "$ProjectPath\frontend\src\app\(dashboard)" "Dashboard routes"
New-DirectoryStructure "$ProjectPath\frontend\src\app\api" "API route handlers"

# Components and UI
New-DirectoryStructure "$ProjectPath\frontend\src\components" "React components"
New-DirectoryStructure "$ProjectPath\frontend\src\components\ui" "UI components"
New-DirectoryStructure "$ProjectPath\frontend\src\components\forms" "Form components"
New-DirectoryStructure "$ProjectPath\frontend\src\components\layout" "Layout components"
New-DirectoryStructure "$ProjectPath\frontend\src\components\charts" "Chart components"
New-DirectoryStructure "$ProjectPath\frontend\src\components\legal" "Legal-specific components"

# Application logic
New-DirectoryStructure "$ProjectPath\frontend\src\hooks" "Custom React hooks"
New-DirectoryStructure "$ProjectPath\frontend\src\store" "State management"
New-DirectoryStructure "$ProjectPath\frontend\src\services" "API services"
New-DirectoryStructure "$ProjectPath\frontend\src\utils" "Utility functions"
New-DirectoryStructure "$ProjectPath\frontend\src\lib" "Library configurations"

# Types and interfaces
New-DirectoryStructure "$ProjectPath\frontend\src\types" "TypeScript type definitions"
New-DirectoryStructure "$ProjectPath\frontend\src\interfaces" "Interface definitions"

# Styling and assets
New-DirectoryStructure "$ProjectPath\frontend\src\styles" "CSS and styling files"
New-DirectoryStructure "$ProjectPath\frontend\public" "Static assets"
New-DirectoryStructure "$ProjectPath\frontend\public\icons" "Icon assets"
New-DirectoryStructure "$ProjectPath\frontend\public\images" "Image assets"

# Testing
New-DirectoryStructure "$ProjectPath\frontend\tests" "Frontend tests"
New-DirectoryStructure "$ProjectPath\frontend\tests\components" "Component tests"
New-DirectoryStructure "$ProjectPath\frontend\tests\pages" "Page tests"
New-DirectoryStructure "$ProjectPath\frontend\tests\e2e" "End-to-end tests"
New-DirectoryStructure "$ProjectPath\frontend\tests\fixtures" "Test fixtures"

# Storybook
New-DirectoryStructure "$ProjectPath\frontend\.storybook" "Storybook configuration"
New-DirectoryStructure "$ProjectPath\frontend\stories" "Storybook stories"

# Configuration
New-DirectoryStructure "$ProjectPath\frontend\config" "Frontend configuration"

# =============================================================================
# DOCKER DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating Docker directory structure..." "Header"

New-DirectoryStructure "$ProjectPath\docker\backend" "Backend Docker files"
New-DirectoryStructure "$ProjectPath\docker\frontend" "Frontend Docker files"
New-DirectoryStructure "$ProjectPath\docker\nginx" "Nginx configuration"
New-DirectoryStructure "$ProjectPath\docker\nginx\conf.d" "Nginx server configs"
New-DirectoryStructure "$ProjectPath\docker\nginx\ssl" "SSL certificates"
New-DirectoryStructure "$ProjectPath\docker\postgres" "PostgreSQL configuration"
New-DirectoryStructure "$ProjectPath\docker\redis" "Redis configuration"
New-DirectoryStructure "$ProjectPath\docker\minio" "MinIO configuration"
New-DirectoryStructure "$ProjectPath\docker\monitoring" "Monitoring stack configs"
New-DirectoryStructure "$ProjectPath\docker\prometheus" "Prometheus configuration"
New-DirectoryStructure "$ProjectPath\docker\grafana" "Grafana dashboards and config"
New-DirectoryStructure "$ProjectPath\docker\grafana\dashboards" "Grafana dashboard definitions"
New-DirectoryStructure "$ProjectPath\docker\grafana\datasources" "Grafana data source configs"

# =============================================================================
# KUBERNETES DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating Kubernetes directory structure..." "Header"

New-DirectoryStructure "$ProjectPath\kubernetes\base" "Base Kubernetes manifests"
New-DirectoryStructure "$ProjectPath\kubernetes\overlays" "Kustomize overlays"
New-DirectoryStructure "$ProjectPath\kubernetes\overlays\development" "Development environment"
New-DirectoryStructure "$ProjectPath\kubernetes\overlays\staging" "Staging environment"
New-DirectoryStructure "$ProjectPath\kubernetes\overlays\production" "Production environment"
New-DirectoryStructure "$ProjectPath\kubernetes\secrets" "Secret manifests"
New-DirectoryStructure "$ProjectPath\kubernetes\configmaps" "ConfigMap manifests"
New-DirectoryStructure "$ProjectPath\kubernetes\ingress" "Ingress configurations"
New-DirectoryStructure "$ProjectPath\kubernetes\monitoring" "Monitoring stack"
New-DirectoryStructure "$ProjectPath\kubernetes\storage" "Persistent volume configs"

# =============================================================================
# SCRIPTS DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating scripts directory structure..." "Header"

New-DirectoryStructure "$ProjectPath\scripts\setup" "Setup and installation scripts"
New-DirectoryStructure "$ProjectPath\scripts\deploy" "Deployment scripts"
New-DirectoryStructure "$ProjectPath\scripts\backup" "Backup and restore scripts"
New-DirectoryStructure "$ProjectPath\scripts\migration" "Data migration scripts"
New-DirectoryStructure "$ProjectPath\scripts\monitoring" "Monitoring and health check scripts"
New-DirectoryStructure "$ProjectPath\scripts\development" "Development utility scripts"
New-DirectoryStructure "$ProjectPath\scripts\testing" "Testing automation scripts"
New-DirectoryStructure "$ProjectPath\scripts\ci-cd" "CI/CD pipeline scripts"

# =============================================================================
# DOCUMENTATION DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating documentation directory structure..." "Header"

New-DirectoryStructure "$ProjectPath\docs\api" "API documentation"
New-DirectoryStructure "$ProjectPath\docs\architecture" "Architecture diagrams and docs"
New-DirectoryStructure "$ProjectPath\docs\deployment" "Deployment guides"
New-DirectoryStructure "$ProjectPath\docs\development" "Development guides"
New-DirectoryStructure "$ProjectPath\docs\user-guides" "User documentation"
New-DirectoryStructure "$ProjectPath\docs\legal" "Legal and compliance docs"
New-DirectoryStructure "$ProjectPath\docs\security" "Security documentation"
New-DirectoryStructure "$ProjectPath\docs\troubleshooting" "Troubleshooting guides"
New-DirectoryStructure "$ProjectPath\docs\changelog" "Release notes and changelogs"
New-DirectoryStructure "$ProjectPath\docs\assets" "Documentation assets"
New-DirectoryStructure "$ProjectPath\docs\assets\images" "Images and diagrams"
New-DirectoryStructure "$ProjectPath\docs\assets\videos" "Video tutorials"

# =============================================================================
# MONITORING DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating monitoring directory structure..." "Header"

New-DirectoryStructure "$ProjectPath\monitoring\prometheus" "Prometheus configuration"
New-DirectoryStructure "$ProjectPath\monitoring\grafana" "Grafana configuration"
New-DirectoryStructure "$ProjectPath\monitoring\alertmanager" "Alert manager configuration"
New-DirectoryStructure "$ProjectPath\monitoring\jaeger" "Distributed tracing"
New-DirectoryStructure "$ProjectPath\monitoring\elk" "ELK stack configuration"
New-DirectoryStructure "$ProjectPath\monitoring\dashboards" "Custom dashboards"
New-DirectoryStructure "$ProjectPath\monitoring\rules" "Alerting rules"

# =============================================================================
# DATA DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating data directory structure..." "Header"

New-DirectoryStructure "$ProjectPath\data\samples" "Sample data files"
New-DirectoryStructure "$ProjectPath\data\legal" "Legal document samples"
New-DirectoryStructure "$ProjectPath\data\contracts" "Contract templates"
New-DirectoryStructure "$ProjectPath\data\cases" "Legal case samples"
New-DirectoryStructure "$ProjectPath\data\citations" "Citation databases"
New-DirectoryStructure "$ProjectPath\data\exports" "Data export files"
New-DirectoryStructure "$ProjectPath\data\imports" "Data import staging"

# =============================================================================
# STORAGE DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating storage directory structure..." "Header"

New-DirectoryStructure "$ProjectPath\storage\documents" "Document storage"
New-DirectoryStructure "$ProjectPath\storage\temp" "Temporary files"
New-DirectoryStructure "$ProjectPath\storage\cache" "File cache"
New-DirectoryStructure "$ProjectPath\storage\uploads" "User uploads"
New-DirectoryStructure "$ProjectPath\storage\processed" "Processed documents"
New-DirectoryStructure "$ProjectPath\storage\exports" "Export files"

# =============================================================================
# CI/CD DIRECTORY STRUCTURE
# =============================================================================

Write-ColorOutput "`nCreating CI/CD directory structure..." "Header"

New-DirectoryStructure "$ProjectPath\.github\workflows" "GitHub Actions workflows"
New-DirectoryStructure "$ProjectPath\.github\ISSUE_TEMPLATE" "Issue templates"
New-DirectoryStructure "$ProjectPath\.github\PULL_REQUEST_TEMPLATE" "PR templates"
New-DirectoryStructure "$ProjectPath\ci\jenkins" "Jenkins pipeline scripts"
New-DirectoryStructure "$ProjectPath\ci\gitlab" "GitLab CI configuration"
New-DirectoryStructure "$ProjectPath\ci\azure" "Azure DevOps pipelines"

# =============================================================================
# CONFIGURATION FILES
# =============================================================================

Write-ColorOutput "`nCreating configuration directories..." "Header"

New-DirectoryStructure "$ProjectPath\config\environments" "Environment-specific configs"
New-DirectoryStructure "$ProjectPath\config\nginx" "Nginx configuration files"
New-DirectoryStructure "$ProjectPath\config\ssl" "SSL certificate storage"
New-DirectoryStructure "$ProjectPath\config\logging" "Logging configurations"

# =============================================================================
# CREATE PLACEHOLDER FILES
# =============================================================================

Write-ColorOutput "`nCreating placeholder files..." "Header"

# Root level placeholder files
New-PlaceholderFile "$ProjectPath\backend\__init__.py" ""
New-PlaceholderFile "$ProjectPath\backend\main.py" "# FastAPI main application entry point"
New-PlaceholderFile "$ProjectPath\frontend\next.config.js" "// Next.js configuration"
New-PlaceholderFile "$ProjectPath\terraform\main.tf" "# Terraform main configuration"
New-PlaceholderFile "$ProjectPath\kubernetes\kustomization.yaml" "# Kustomize configuration"

# Docker files
New-PlaceholderFile "$ProjectPath\docker\backend\Dockerfile" "# FastAPI Backend Dockerfile"
New-PlaceholderFile "$ProjectPath\docker\frontend\Dockerfile" "# Next.js Frontend Dockerfile"

# Keep files for empty directories
New-PlaceholderFile "$ProjectPath\storage\.gitkeep" ""
New-PlaceholderFile "$ProjectPath\logs\.gitkeep" ""
New-PlaceholderFile "$ProjectPath\backups\.gitkeep" ""
New-PlaceholderFile "$ProjectPath\secrets\.gitkeep" ""

# Documentation index files
New-PlaceholderFile "$ProjectPath\docs\README.md" "# Legal AI System Documentation"
New-PlaceholderFile "$ProjectPath\docs\api\README.md" "# API Documentation"
New-PlaceholderFile "$ProjectPath\docs\architecture\README.md" "# Architecture Documentation"

# =============================================================================
# COMPLETION MESSAGE
# =============================================================================

Write-ColorOutput "`n=============================================================================`n" "Header"
Write-ColorOutput "PROJECT STRUCTURE CREATION COMPLETED!" "Success"
Write-ColorOutput "`n=============================================================================`n" "Header"

if ($WhatIf) {
    Write-ColorOutput "This was a dry run. No files or directories were actually created." "Warning"
    Write-ColorOutput "Run the script without -WhatIf to create the actual structure." "Info"
} else {
    Write-ColorOutput "Legal AI System project structure has been created successfully!" "Success"
    Write-ColorOutput "`nNext steps:" "Info"
    Write-ColorOutput "1. Review the .gitignore file to ensure proper exclusions" "Info"
    Write-ColorOutput "2. Set up your development environment" "Info"
    Write-ColorOutput "3. Configure your IDE/editor for the project structure" "Info"
    Write-ColorOutput "4. Start developing your Legal AI System!" "Info"
}

Write-ColorOutput "`nProject root: $ProjectPath" "Info"
Write-ColorOutput "`n=============================================================================`n" "Header"