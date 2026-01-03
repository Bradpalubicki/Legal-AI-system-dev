# Legal AI System - Kubernetes Deployment

This directory contains comprehensive Kubernetes deployment configurations for the Legal AI System, providing production-ready containerized orchestration with monitoring, security, and scalability.

## 📋 Overview

The Kubernetes deployment includes:
- **Multi-tier Architecture**: Backend API, Frontend web app, Database, Cache, Storage, Workers
- **Environment-specific Configurations**: Production, Staging, Development overlays
- **Auto-scaling**: Horizontal Pod Autoscaling based on CPU, memory, and custom metrics
- **High Availability**: Pod Disruption Budgets and anti-affinity rules
- **Security**: Network policies, RBAC, secret management
- **Monitoring**: Prometheus + Grafana observability stack
- **SSL/TLS**: Automatic certificate management with cert-manager

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Ingress       │    │   Frontend      │    │   Backend API   │
│   (NGINX)       │───▶│   (Next.js)     │───▶│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   PostgreSQL    │    │   Redis Cache   │
│   (Kubernetes)  │    │   (Database)    │    │   (Sessions)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │                       │
                                 ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   MinIO Storage │    │   Celery Workers│
                       │   (Documents)   │    │   (Background)  │
                       └─────────────────┘    └─────────────────┘
```

## 📁 Directory Structure

```
kubernetes/
├── base/                          # Base Kubernetes manifests
│   ├── namespace.yaml            # Namespace and resource quotas
│   ├── rbac.yaml                 # Service accounts and RBAC
│   ├── postgres-deployment.yaml  # PostgreSQL database
│   ├── redis-deployment.yaml     # Redis cache
│   ├── minio-deployment.yaml     # MinIO object storage
│   ├── backend-deployment.yaml   # FastAPI backend
│   ├── frontend-deployment.yaml  # Next.js frontend
│   ├── celery-*.yaml            # Background workers
│   ├── nginx-deployment.yaml     # Reverse proxy
│   └── kustomization.yaml        # Base kustomization
│
├── configmaps/                   # Configuration files
│   ├── postgres-config.yaml     # Database configuration
│   ├── redis-config.yaml        # Cache configuration
│   ├── backend-config.yaml      # API configuration
│   ├── frontend-config.yaml     # Web app configuration
│   └── nginx-config.yaml        # Reverse proxy config
│
├── secrets/                      # Secret templates
│   ├── database-secret.yaml     # Database credentials
│   ├── redis-secret.yaml        # Cache configuration
│   ├── minio-secret.yaml        # Storage credentials
│   └── api-keys-secret.yaml     # API keys and tokens
│
├── storage/                      # Persistent storage
│   ├── postgres-pv.yaml         # Database storage
│   ├── redis-pv.yaml           # Cache storage
│   └── minio-pv.yaml           # Object storage
│
├── ingress/                      # Network ingress
│   └── ingress.yaml             # NGINX ingress with SSL
│
├── monitoring/                   # Observability stack
│   ├── prometheus-deployment.yaml # Metrics collection
│   ├── grafana-deployment.yaml   # Visualization
│   └── alerting-rules.yaml       # Alert definitions
│
└── overlays/                     # Environment-specific configs
    ├── production/               # Production environment
    │   ├── kustomization.yaml   # Production overrides
    │   ├── hpa.yaml            # Auto-scaling rules
    │   ├── pdb.yaml            # Disruption budgets
    │   └── ingress-production.yaml
    ├── staging/                  # Staging environment
    │   └── kustomization.yaml   # Staging overrides
    └── development/              # Development environment
        └── kustomization.yaml   # Development overrides
```

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes Cluster** (v1.24+)
   ```bash
   # Verify cluster access
   kubectl cluster-info
   kubectl get nodes
   ```

2. **Required Tools**
   ```bash
   # Install kustomize
   kubectl kustomize --help
   
   # Install cert-manager (for SSL certificates)
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

3. **Storage Classes**
   ```bash
   # Verify available storage classes
   kubectl get storageclass
   
   # Example: Create fast-ssd storage class (GKE)
   kubectl apply -f - <<EOF
   apiVersion: storage.k8s.io/v1
   kind: StorageClass
   metadata:
     name: fast-ssd
   provisioner: kubernetes.io/gce-pd
   parameters:
     type: pd-ssd
     replication-type: none
   EOF
   ```

### Deployment Steps

1. **Update Configuration**
   ```bash
   # Copy and customize environment variables
   cp kubernetes/secrets/database-secret.yaml.example kubernetes/secrets/database-secret.yaml
   cp kubernetes/secrets/api-keys-secret.yaml.example kubernetes/secrets/api-keys-secret.yaml
   
   # Update with your actual secrets
   # NEVER commit real secrets to version control!
   ```

2. **Deploy to Development**
   ```bash
   # Apply development configuration
   kubectl apply -k kubernetes/overlays/development/
   
   # Verify deployment
   kubectl get pods -n legal-ai-dev
   kubectl get services -n legal-ai-dev
   ```

3. **Deploy to Production**
   ```bash
   # Update production secrets (use external secret management)
   # Apply production configuration
   kubectl apply -k kubernetes/overlays/production/
   
   # Verify deployment
   kubectl get pods -n legal-ai-system
   kubectl get ingress -n legal-ai-system
   ```

4. **Access Applications**
   ```bash
   # Get ingress IP
   kubectl get ingress legal-ai-ingress -n legal-ai-system
   
   # Port forward for local development
   kubectl port-forward -n legal-ai-system svc/frontend-service 3000:3000
   kubectl port-forward -n legal-ai-system svc/backend-service 8000:8000
   ```

## ⚙️ Configuration

### Environment Variables

Key configuration is managed through ConfigMaps and Secrets:

- **Database**: Connection strings, pool sizes, SSL settings
- **Redis**: Cache configuration, session management
- **API Keys**: OpenAI, Anthropic, legal databases (Westlaw, LexisNexis)
- **Security**: JWT secrets, encryption keys, CORS settings
- **Storage**: MinIO credentials, bucket configuration
- **Monitoring**: Prometheus, Grafana, alerting

### Resource Allocation

| Environment | Backend | Frontend | Workers | Database | Total |
|-------------|---------|----------|---------|----------|-------|
| Development | 1 pod   | 1 pod    | 1 pod   | 1 pod    | ~2GB  |
| Staging     | 2 pods  | 2 pods   | 2 pods  | 1 pod    | ~4GB  |
| Production  | 3-10 pods| 2-8 pods | 3-15 pods| 1 pod   | 8-32GB|

### Auto-scaling

Production environment includes Horizontal Pod Autoscaling:

- **Backend**: 3-10 pods based on CPU (70%), memory (80%), HTTP requests
- **Frontend**: 2-8 pods based on CPU/memory
- **Workers**: 3-15 pods based on CPU/memory and Celery queue length

## 🔒 Security

### Network Security

- **Network Policies**: Restrict pod-to-pod communication
- **Ingress Security**: Rate limiting, SSL termination
- **Service Mesh**: Optional Istio integration for advanced security

### Secret Management

```bash
# Use external secret management in production
# Example with AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-west-2
```

### RBAC

Minimal privilege service accounts:
- Separate accounts for each service
- Read-only access where possible
- No cluster-admin privileges

## 📊 Monitoring

### Prometheus Metrics

The system exposes comprehensive metrics:

- **Application**: HTTP requests, response times, error rates
- **Business**: Document processing, AI analysis, user activity
- **Infrastructure**: CPU, memory, disk, network
- **Database**: Connections, query performance, locks

### Grafana Dashboards

Pre-configured dashboards for:
- Legal AI System Overview
- Application Performance
- Database Performance
- Celery Worker Monitoring
- Infrastructure Health

### Alerting

Key alerts configured:
- High CPU/Memory usage
- Pod restart loops
- Database connection issues
- Celery queue buildup
- Disk space warnings
- SSL certificate expiration

## 🚨 Troubleshooting

### Common Issues

1. **Pod Startup Failures**
   ```bash
   kubectl describe pod <pod-name> -n legal-ai-system
   kubectl logs <pod-name> -n legal-ai-system --previous
   ```

2. **Database Connection Issues**
   ```bash
   kubectl exec -it deployment/postgres -n legal-ai-system -- psql -U legalai_user -d legal_ai_system
   ```

3. **Storage Issues**
   ```bash
   kubectl get pv,pvc -n legal-ai-system
   kubectl describe pvc <pvc-name> -n legal-ai-system
   ```

4. **Ingress Issues**
   ```bash
   kubectl describe ingress legal-ai-ingress -n legal-ai-system
   kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
   ```

### Health Checks

```bash
# Overall system health
kubectl get pods -n legal-ai-system
kubectl get services -n legal-ai-system
kubectl top pods -n legal-ai-system

# Application health endpoints
curl https://legal-ai.example.com/api/health
curl https://legal-ai.example.com/health
```

## 📈 Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n legal-ai-system

# Scale workers
kubectl scale deployment celery-worker --replicas=10 -n legal-ai-system
```

### Cluster Scaling

For production workloads, ensure cluster has adequate resources:

- **Minimum**: 3 nodes, 8 CPU cores, 16GB RAM
- **Recommended**: 5+ nodes, 16+ CPU cores, 32GB+ RAM
- **Storage**: SSD-backed persistent volumes

## 🔄 Updates

### Rolling Updates

```bash
# Update backend image
kubectl set image deployment/backend backend=legal-ai-backend:1.1.0 -n legal-ai-system

# Monitor rollout
kubectl rollout status deployment/backend -n legal-ai-system

# Rollback if needed
kubectl rollout undo deployment/backend -n legal-ai-system
```

### Configuration Updates

```bash
# Update ConfigMap
kubectl apply -k kubernetes/overlays/production/

# Restart deployments to pick up config changes
kubectl rollout restart deployment/backend -n legal-ai-system
```

## 📝 Maintenance

### Regular Tasks

- **Certificate Renewal**: Automated with cert-manager
- **Database Backups**: Scheduled via CronJob
- **Log Rotation**: Configured in container runtime
- **Security Updates**: Regular base image updates
- **Monitoring Review**: Weekly dashboard and alert review

### Backup Strategy

- **Database**: Daily automated backups to S3
- **Object Storage**: Cross-region replication
- **Configuration**: GitOps approach with version control
- **Disaster Recovery**: Multi-AZ deployment capability

## 🔗 External Dependencies

- **DNS**: Configure A/CNAME records for your domain
- **SSL Certificates**: Let's Encrypt via cert-manager or custom certificates
- **External APIs**: OpenAI, Anthropic, Westlaw, LexisNexis API keys
- **Email**: SMTP configuration for notifications
- **Storage**: S3-compatible storage for backups

## 📞 Support

For deployment issues:
1. Check logs: `kubectl logs <pod-name> -n legal-ai-system`
2. Review events: `kubectl get events -n legal-ai-system --sort-by='.lastTimestamp'`
3. Check resource usage: `kubectl top pods -n legal-ai-system`
4. Validate configuration: `kubectl apply --dry-run=client -k kubernetes/overlays/production/`

---

**Security Notice**: Never commit real secrets to version control. Use external secret management systems in production environments.