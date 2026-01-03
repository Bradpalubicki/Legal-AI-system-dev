# Deployment Runbook - Legal AI System

**Status:** ✅ Ready for Production
**Priority:** Critical (Operations)
**Last Updated:** 2025-10-14

## Overview

This runbook provides step-by-step procedures for deploying the Legal AI System to various environments, including rollback procedures, verification steps, and troubleshooting guidance.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Overview](#environment-overview)
3. [Deployment Procedures](#deployment-procedures)
4. [Database Migrations](#database-migrations)
5. [Zero-Downtime Deployment](#zero-downtime-deployment)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Troubleshooting](#troubleshooting)
9. [Emergency Procedures](#emergency-procedures)

---

## Pre-Deployment Checklist

### Code Quality Gates

Before deploying to any environment, ensure:

- [ ] All tests passing (backend and frontend)
  ```bash
  # Backend tests
  cd backend && pytest -v

  # Frontend tests
  cd frontend && npm test
  ```

- [ ] Code coverage meets minimum threshold (80%)
  ```bash
  cd backend && pytest --cov=app --cov-report=term-missing
  ```

- [ ] Linting passes with no errors
  ```bash
  # Backend
  cd backend && flake8 app/

  # Frontend
  cd frontend && npm run lint
  ```

- [ ] Type checking passes
  ```bash
  # Backend
  cd backend && mypy app/

  # Frontend
  cd frontend && npm run typecheck
  ```

- [ ] Security scan completed (no critical vulnerabilities)
  ```bash
  # Backend dependencies
  cd backend && pip-audit

  # Frontend dependencies
  cd frontend && npm audit --production
  ```

- [ ] Code reviewed and approved by at least 2 team members

- [ ] All required environment variables documented in `.env.example`

### Documentation Requirements

- [ ] CHANGELOG.md updated with release notes
- [ ] API documentation updated (if API changes)
- [ ] Database migration scripts created and tested
- [ ] Runbooks updated for new features
- [ ] User-facing documentation updated

### Infrastructure Readiness

- [ ] Database backup completed successfully
- [ ] Sufficient disk space available (>20% free)
- [ ] Monitoring dashboards configured
- [ ] Alert rules reviewed and updated
- [ ] On-call engineer assigned and available
- [ ] Rollback plan documented and understood

### Communication

- [ ] Deployment window scheduled and communicated
- [ ] Stakeholders notified (if customer-facing changes)
- [ ] Maintenance page prepared (if downtime expected)
- [ ] Post-deployment communication template ready

---

## Environment Overview

### Development
- **Purpose**: Local development and testing
- **URL**: http://localhost:3000
- **Database**: Local PostgreSQL
- **Deployment**: Manual (Docker Compose)
- **Monitoring**: None
- **Backups**: None

### Staging
- **Purpose**: Pre-production testing and validation
- **URL**: https://staging.legal-ai-system.com
- **Database**: Staging PostgreSQL (isolated)
- **Deployment**: Automated via CI/CD
- **Monitoring**: Full monitoring (Prometheus, Grafana)
- **Backups**: Daily

### Production
- **Purpose**: Live customer-facing environment
- **URL**: https://legal-ai-system.com
- **Database**: Production PostgreSQL (primary + read replica)
- **Deployment**: Blue-green deployment via CI/CD
- **Monitoring**: Full monitoring + alerting
- **Backups**: Hourly + point-in-time recovery

---

## Deployment Procedures

### Development Deployment

**Purpose**: Local testing and development

**Steps**:

1. **Pull latest code**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Update dependencies**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt

   # Frontend
   cd frontend
   npm install
   ```

3. **Run database migrations**
   ```bash
   cd backend
   alembic upgrade head
   ```

4. **Start services**
   ```bash
   docker-compose up --build
   ```

5. **Verify deployment**
   - Backend health: http://localhost:8000/health
   - Frontend: http://localhost:3000

### Staging Deployment

**Purpose**: Pre-production validation

**Trigger**: Merge to `staging` branch

**Automated CI/CD Pipeline**:

```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging

on:
  push:
    branches: [staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run tests
        run: |
          cd backend && pytest
          cd ../frontend && npm test

      - name: Build Docker images
        run: |
          docker build -t legal-ai-backend:staging ./backend
          docker build -t legal-ai-frontend:staging ./frontend

      - name: Push to registry
        run: |
          docker push legal-ai-backend:staging
          docker push legal-ai-frontend:staging

      - name: Run database migrations
        run: |
          kubectl exec -n staging deployment/backend -- alembic upgrade head

      - name: Deploy to Kubernetes
        run: |
          kubectl apply -f k8s/staging/

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/backend -n staging
          kubectl rollout status deployment/frontend -n staging

      - name: Run smoke tests
        run: |
          ./scripts/smoke-tests.sh https://staging.legal-ai-system.com

      - name: Notify team
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "✅ Staging deployment completed successfully",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Staging Deployment*\nCommit: ${{ github.sha }}\nStatus: Success"
                  }
                }
              ]
            }
```

**Manual Steps**:

1. **Create staging branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b staging
   git push origin staging
   ```

2. **Monitor deployment**
   - Watch GitHub Actions: https://github.com/legal-ai-system/actions
   - Check logs: `kubectl logs -f deployment/backend -n staging`
   - Monitor Grafana dashboard

3. **Verify deployment**
   ```bash
   # Health checks
   curl https://staging.legal-ai-system.com/health
   curl https://staging.legal-ai-system.com/api/health

   # Database connectivity
   curl https://staging.legal-ai-system.com/api/health/database
   ```

4. **Run integration tests**
   ```bash
   npm run test:integration -- --env=staging
   ```

### Production Deployment

**Purpose**: Release to customers

**Trigger**: Manual approval after successful staging deployment

**Deployment Strategy**: Blue-Green Deployment

**Pre-Deployment**:

1. **Create release branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b release/v1.2.0
   ```

2. **Update version**
   ```bash
   # Update version in package.json, pyproject.toml, etc.
   # Commit version bump
   git commit -am "chore: bump version to 1.2.0"
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin release/v1.2.0 --tags
   ```

3. **Schedule maintenance window** (if downtime required)
   ```bash
   # Create Alertmanager silence
   curl -X POST https://alertmanager.legal-ai-system.com/api/v1/silences \
     -d '{
       "matchers": [{"name": "severity", "value": "warning", "isRegex": false}],
       "startsAt": "2025-10-14T02:00:00Z",
       "endsAt": "2025-10-14T04:00:00Z",
       "createdBy": "deployment-team",
       "comment": "Scheduled deployment v1.2.0"
     }'
   ```

4. **Backup production database**
   ```bash
   # Automatic backup via script
   ./scripts/backup-production-db.sh

   # Verify backup
   ./scripts/verify-backup.sh latest
   ```

**Deployment Steps**:

1. **Deploy to green environment**
   ```bash
   # Green environment uses separate deployment
   kubectl apply -f k8s/production/green/

   # Wait for green deployment
   kubectl rollout status deployment/backend-green -n production
   kubectl rollout status deployment/frontend-green -n production
   ```

2. **Run database migrations on green**
   ```bash
   # Migrations are backward-compatible
   kubectl exec -n production deployment/backend-green -- alembic upgrade head
   ```

3. **Warm up green environment**
   ```bash
   # Send synthetic traffic to warm caches
   ./scripts/warmup-deployment.sh green
   ```

4. **Run smoke tests on green**
   ```bash
   # Test green environment (not yet public)
   ./scripts/smoke-tests.sh https://green.internal.legal-ai-system.com
   ```

5. **Monitor green environment**
   - Check logs: `kubectl logs -f deployment/backend-green -n production`
   - Check metrics: Grafana dashboard (Green Environment)
   - Verify no errors in Sentry

6. **Switch traffic to green** (Blue-Green Cutover)
   ```bash
   # Update ingress to point to green
   kubectl patch ingress legal-ai-ingress -n production \
     --type='json' -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value":"frontend-green"}]'

   # Verify traffic switch
   curl -I https://legal-ai-system.com | grep X-Deployment-Color
   # Should return: X-Deployment-Color: green
   ```

7. **Monitor production traffic**
   - Watch error rates (should be <0.1%)
   - Watch latency (P95 should be <500ms)
   - Monitor Sentry for new errors
   - Check user reports/support tickets

8. **Keep blue environment running** (30 minutes)
   - Allow for quick rollback if needed
   - Monitor green environment closely

9. **Decommission blue environment** (if deployment successful)
   ```bash
   # After 30 minutes of successful green deployment
   kubectl scale deployment/backend-blue --replicas=0 -n production
   kubectl scale deployment/frontend-blue --replicas=0 -n production
   ```

10. **Post-deployment tasks**
    - Update documentation
    - Close deployment ticket
    - Notify stakeholders
    - Update on-call runbooks

---

## Database Migrations

### Migration Strategy

**Approach**: Expand-Contract Pattern (Zero-Downtime)

1. **Expand**: Add new schema elements (backward-compatible)
2. **Deploy**: Deploy new code that supports both old and new schema
3. **Migrate**: Migrate data from old to new schema
4. **Contract**: Remove old schema elements (in next release)

### Creating Migrations

```bash
# Generate migration automatically
cd backend
alembic revision --autogenerate -m "Add user preferences table"

# Edit generated migration file
# backend/alembic/versions/xxxx_add_user_preferences_table.py

# Test migration locally
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

### Migration Best Practices

**DO**:
- ✅ Make migrations backward-compatible
- ✅ Test migrations on production-like data
- ✅ Include rollback logic in `downgrade()`
- ✅ Use batching for large data migrations
- ✅ Add indexes CONCURRENTLY (PostgreSQL)
- ✅ Validate data after migration

**DON'T**:
- ❌ Drop columns in same release as code change
- ❌ Rename columns directly (use multi-step process)
- ❌ Lock tables for extended periods
- ❌ Migrate large datasets synchronously
- ❌ Deploy migrations without testing

### Running Migrations in Production

**Manual Migration** (if not automated):

```bash
# 1. Backup database first
./scripts/backup-production-db.sh

# 2. Connect to production database pod
kubectl exec -it deployment/backend -n production -- bash

# 3. Check pending migrations
alembic current
alembic heads

# 4. Run migrations
alembic upgrade head

# 5. Verify migration
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"

# 6. Test application
curl https://legal-ai-system.com/health/database
```

**Automated Migration** (via CI/CD):

```yaml
# .github/workflows/deploy-production.yml
- name: Run database migrations
  run: |
    kubectl exec -n production deployment/backend -- \
      alembic upgrade head

- name: Verify migration
  run: |
    kubectl exec -n production deployment/backend -- \
      alembic current
```

### Rolling Back Migrations

```bash
# Rollback last migration
kubectl exec -n production deployment/backend -- alembic downgrade -1

# Rollback to specific version
kubectl exec -n production deployment/backend -- alembic downgrade abc123def456

# Verify rollback
kubectl exec -n production deployment/backend -- alembic current
```

---

## Zero-Downtime Deployment

### Strategy

Use **Blue-Green Deployment** for zero-downtime:

1. **Blue** (current): Serving production traffic
2. **Green** (new): New version deployed and tested
3. **Switch**: Traffic instantly switched from blue to green
4. **Rollback**: If issues, instantly switch back to blue

### Implementation

**Kubernetes Configuration**:

```yaml
# k8s/production/blue/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-blue
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
      color: blue
  template:
    metadata:
      labels:
        app: backend
        color: blue
    spec:
      containers:
      - name: backend
        image: legal-ai-backend:v1.1.0
        # ... container spec

---
# k8s/production/green/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-green
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
      color: green
  template:
    metadata:
      labels:
        app: backend
        color: green
    spec:
      containers:
      - name: backend
        image: legal-ai-backend:v1.2.0
        # ... container spec

---
# k8s/production/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: production
spec:
  selector:
    app: backend
    color: blue  # Switch this to 'green' for cutover
  ports:
  - port: 8000
    targetPort: 8000
```

**Traffic Switch Script**:

```bash
#!/bin/bash
# scripts/switch-deployment-color.sh

COLOR=$1  # 'blue' or 'green'

echo "Switching traffic to $COLOR environment..."

# Update service selector
kubectl patch service backend -n production \
  --type='json' \
  -p="[{\"op\": \"replace\", \"path\": \"/spec/selector/color\", \"value\":\"$COLOR\"}]"

kubectl patch service frontend -n production \
  --type='json' \
  -p="[{\"op\": \"replace\", \"path\": \"/spec/selector/color\", \"value\":\"$COLOR\"}]"

echo "Traffic switched to $COLOR"
echo "Monitoring for 5 minutes..."

# Monitor for errors
sleep 300

# Check error rate
ERROR_RATE=$(promtool query instant \
  'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])')

if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
  echo "ERROR: High error rate detected ($ERROR_RATE)"
  echo "Consider rolling back"
  exit 1
fi

echo "Deployment successful!"
```

### Canary Deployment (Alternative)

Gradually shift traffic to new version:

```yaml
# k8s/production/ingress-canary.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: legal-ai-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% traffic
spec:
  rules:
  - host: legal-ai-system.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-green
            port:
              number: 3000
```

**Gradual Traffic Shift**:

```bash
# 10% traffic
kubectl patch ingress legal-ai-canary -n production \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"10"}}}'

# Wait 10 minutes, monitor metrics

# 25% traffic
kubectl patch ingress legal-ai-canary -n production \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"25"}}}'

# Wait 10 minutes, monitor metrics

# 50% traffic
kubectl patch ingress legal-ai-canary -n production \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"50"}}}'

# Wait 10 minutes, monitor metrics

# 100% traffic (complete cutover)
kubectl patch ingress legal-ai-canary -n production \
  -p '{"metadata":{"annotations":{"nginx.ingress.kubernetes.io/canary-weight":"100"}}}'
```

---

## Rollback Procedures

### When to Rollback

Rollback immediately if:
- Error rate >1% for 5 minutes
- Critical functionality broken
- Data corruption detected
- Security vulnerability introduced
- P95 latency >5 seconds for 10 minutes

### Automatic Rollback Criteria

```yaml
# Automated rollback via monitoring
- alert: DeploymentFailure
  expr: |
    (
      rate(http_requests_total{status=~"5.."}[5m])
      /
      rate(http_requests_total[5m])
    ) > 0.01
  for: 5m
  labels:
    severity: critical
    action: rollback
  annotations:
    summary: "High error rate - triggering automatic rollback"
```

### Blue-Green Rollback

**Instant Rollback** (switch back to blue):

```bash
# Switch traffic back to blue environment
./scripts/switch-deployment-color.sh blue

# Verify rollback
curl -I https://legal-ai-system.com | grep X-Deployment-Color
# Should return: X-Deployment-Color: blue

# Monitor for recovery
watch -n 5 'curl -s https://legal-ai-system.com/health'
```

**Complete Rollback** (< 1 minute):

```bash
# 1. Switch ingress to blue
kubectl patch service backend -n production \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/selector/color", "value":"blue"}]'

# 2. Verify traffic switched
kubectl get svc backend -n production -o yaml | grep color

# 3. Scale up blue (if scaled down)
kubectl scale deployment/backend-blue --replicas=3 -n production
kubectl scale deployment/frontend-blue --replicas=3 -n production

# 4. Wait for blue to be ready
kubectl rollout status deployment/backend-blue -n production

# 5. Verify service health
curl https://legal-ai-system.com/health

# 6. Scale down green
kubectl scale deployment/backend-green --replicas=0 -n production
kubectl scale deployment/frontend-green --replicas=0 -n production
```

### Database Rollback

**Rollback Migration**:

```bash
# 1. Backup current state
./scripts/backup-production-db.sh

# 2. Rollback migration
kubectl exec -n production deployment/backend -- \
  alembic downgrade -1

# 3. Verify rollback
kubectl exec -n production deployment/backend -- \
  alembic current

# 4. Test application
curl https://legal-ai-system.com/health/database
```

**Restore from Backup** (if migration rollback fails):

```bash
# 1. Stop application traffic
kubectl scale deployment/backend --replicas=0 -n production

# 2. Restore database from backup
./scripts/restore-production-db.sh backup-2025-10-14-01-00.sql

# 3. Verify restore
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"

# 4. Restart application
kubectl scale deployment/backend --replicas=3 -n production

# 5. Verify health
curl https://legal-ai-system.com/health
```

### Code Rollback

**Rollback to Previous Version**:

```bash
# 1. Get previous version tag
git tag -l | sort -V | tail -2

# 2. Checkout previous version
git checkout v1.1.0

# 3. Build and deploy
docker build -t legal-ai-backend:v1.1.0-rollback ./backend
docker push legal-ai-backend:v1.1.0-rollback

# 4. Update deployment
kubectl set image deployment/backend-green \
  backend=legal-ai-backend:v1.1.0-rollback \
  -n production

# 5. Wait for rollout
kubectl rollout status deployment/backend-green -n production
```

---

## Post-Deployment Verification

### Automated Smoke Tests

```bash
#!/bin/bash
# scripts/smoke-tests.sh

BASE_URL=$1

echo "Running smoke tests against $BASE_URL..."

# 1. Health Check
echo "Testing health endpoint..."
curl -f $BASE_URL/health || exit 1

# 2. API Health
echo "Testing API health..."
curl -f $BASE_URL/api/health || exit 1

# 3. Database Connectivity
echo "Testing database..."
curl -f $BASE_URL/api/health/database || exit 1

# 4. Redis Connectivity
echo "Testing Redis..."
curl -f $BASE_URL/api/health/redis || exit 1

# 5. Authentication
echo "Testing authentication..."
TOKEN=$(curl -s -X POST $BASE_URL/api/auth/login \
  -d '{"username":"test@example.com","password":"testpass"}' \
  | jq -r '.access_token')

if [ -z "$TOKEN" ]; then
  echo "Authentication failed"
  exit 1
fi

# 6. Protected Endpoint
echo "Testing protected endpoint..."
curl -f -H "Authorization: Bearer $TOKEN" \
  $BASE_URL/api/users/me || exit 1

# 7. Document Upload
echo "Testing document upload..."
curl -f -X POST $BASE_URL/api/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test-document.pdf" || exit 1

# 8. AI Analysis
echo "Testing AI analysis..."
curl -f -X POST $BASE_URL/api/documents/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"document_id":"test-doc-123"}' || exit 1

echo "✅ All smoke tests passed!"
```

### Manual Verification

**Checklist**:

- [ ] Homepage loads correctly
- [ ] User can log in
- [ ] User can upload document
- [ ] Document analysis works
- [ ] Search functionality works
- [ ] User profile loads
- [ ] Settings can be updated
- [ ] No console errors in browser
- [ ] No 500 errors in logs
- [ ] Metrics are being collected
- [ ] Alerts are not firing

### Monitoring Checks

```bash
# Check error rate
curl -s 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~"5.."}[5m])' \
  | jq '.data.result[].value[1]'

# Check latency (P95)
curl -s 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))' \
  | jq '.data.result[].value[1]'

# Check active alerts
curl -s 'http://alertmanager:9093/api/v1/alerts' \
  | jq '.data[] | select(.status.state=="active")'
```

### Metrics to Watch (First 2 Hours)

| Metric | Normal Range | Alert Threshold |
|--------|--------------|-----------------|
| Error Rate | <0.1% | >1% |
| P95 Latency | <500ms | >2000ms |
| Request Rate | Baseline ±20% | >200% of baseline |
| Database Connections | <80% | >90% |
| Memory Usage | <70% | >85% |
| CPU Usage | <60% | >80% |

---

## Troubleshooting

### Common Issues

#### Issue 1: Deployment Pod Won't Start

**Symptoms**:
- `kubectl get pods` shows CrashLoopBackOff
- Pods constantly restarting

**Diagnosis**:
```bash
# Check pod status
kubectl describe pod backend-green-xxx -n production

# Check logs
kubectl logs backend-green-xxx -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'
```

**Common Causes**:
1. **Missing environment variables**
   - Fix: Update ConfigMap/Secret
   ```bash
   kubectl edit configmap backend-config -n production
   kubectl rollout restart deployment/backend-green -n production
   ```

2. **Database connection failure**
   - Fix: Check DATABASE_URL, verify network policies
   ```bash
   kubectl exec -it backend-green-xxx -n production -- \
     psql $DATABASE_URL -c "SELECT 1;"
   ```

3. **Insufficient resources**
   - Fix: Increase resource requests/limits
   ```bash
   kubectl edit deployment/backend-green -n production
   # Increase memory/CPU limits
   ```

#### Issue 2: High Error Rate After Deployment

**Symptoms**:
- 500 errors in logs
- Error rate >1%
- Sentry showing new errors

**Diagnosis**:
```bash
# Check error logs
kubectl logs -f deployment/backend-green -n production | grep ERROR

# Check Sentry
open https://sentry.io/legal-ai-system/issues

# Check specific error rate
curl 'http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status="500"}[5m])'
```

**Resolution**:
1. **Immediate**: Rollback to blue
2. **Investigate**: Check Sentry for error details
3. **Fix**: Create hotfix branch
4. **Test**: Deploy to staging first
5. **Redeploy**: After testing in staging

#### Issue 3: Database Migration Failed

**Symptoms**:
- Migration exits with error
- Database schema inconsistent
- Application errors related to database

**Diagnosis**:
```bash
# Check migration status
kubectl exec -n production deployment/backend -- \
  alembic current

# Check migration logs
kubectl logs -f deployment/backend -n production | grep alembic
```

**Resolution**:

1. **Manual intervention required**
   ```bash
   # Connect to database
   kubectl exec -it postgres-0 -n production -- psql legal_ai_system

   # Check alembic version table
   SELECT * FROM alembic_version;

   # Check if partial migration applied
   \dt
   ```

2. **Rollback migration**
   ```bash
   kubectl exec -n production deployment/backend -- \
     alembic downgrade -1
   ```

3. **Fix migration script** and redeploy

4. **If unrecoverable, restore from backup**
   ```bash
   ./scripts/restore-production-db.sh latest
   ```

#### Issue 4: Slow Performance After Deployment

**Symptoms**:
- P95 latency >2 seconds
- Users complaining of slowness
- High database query times

**Diagnosis**:
```bash
# Check latency metrics
curl 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))'

# Check slow queries
kubectl exec -it postgres-0 -n production -- psql legal_ai_system -c \
  "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check connection pool
kubectl logs deployment/backend -n production | grep "connection pool"
```

**Resolution**:

1. **Add missing database indexes**
   ```sql
   CREATE INDEX CONCURRENTLY idx_documents_user_id ON documents(user_id);
   ```

2. **Increase connection pool size**
   ```python
   # Update database settings
   SQLALCHEMY_POOL_SIZE = 20  # from 10
   SQLALCHEMY_MAX_OVERFLOW = 40  # from 20
   ```

3. **Enable query caching**
   ```python
   # Add Redis caching for expensive queries
   @cache.memoize(timeout=300)
   def get_user_documents(user_id):
       # ...
   ```

4. **Scale horizontally**
   ```bash
   kubectl scale deployment/backend --replicas=5 -n production
   ```

---

## Emergency Procedures

### Complete Service Outage

**Severity**: P0 (All hands on deck)

**Immediate Actions** (5 minutes):

1. **Acknowledge incident**
   ```bash
   # Update status page
   curl -X POST https://status.legal-ai-system.com/api/incidents \
     -d '{"status": "investigating", "message": "Service outage"}'
   ```

2. **Page on-call team**
   - Primary on-call
   - Secondary on-call
   - Engineering manager

3. **Create incident channel**
   - Slack: #incident-2025-10-14
   - Invite: DevOps, Backend, Frontend, Product

4. **Assess scope**
   ```bash
   # Check all services
   kubectl get pods --all-namespaces

   # Check external dependencies
   curl https://api.openai.com/v1/models
   curl https://api.anthropic.com/v1/models
   ```

**Recovery Actions**:

1. **Try quick fixes first** (10 minutes)
   - Restart deployments
   - Clear caches
   - Scale up resources

2. **If unsuccessful, rollback** (15 minutes)
   ```bash
   # Rollback to last known good version
   ./scripts/emergency-rollback.sh
   ```

3. **If rollback fails, restore from backup** (30 minutes)
   ```bash
   # Stop all services
   kubectl scale deployment --all --replicas=0 -n production

   # Restore database
   ./scripts/restore-production-db.sh latest

   # Restart services
   kubectl scale deployment --all --replicas=3 -n production
   ```

4. **Update stakeholders** (every 15 minutes)
   - Status page
   - Email to customers
   - Internal updates

### Data Corruption Detected

**Severity**: P1 (Urgent)

**Immediate Actions**:

1. **Stop writes to database**
   ```bash
   # Enable read-only mode
   psql $DATABASE_URL -c "ALTER DATABASE legal_ai_system SET default_transaction_read_only = on;"
   ```

2. **Assess damage**
   ```sql
   -- Check affected records
   SELECT COUNT(*) FROM documents WHERE updated_at > '2025-10-14 01:00:00';
   ```

3. **Backup current state** (before any fixes)
   ```bash
   ./scripts/backup-production-db.sh corruption-$(date +%s)
   ```

4. **Restore from last good backup**
   ```bash
   # Restore to point-in-time before corruption
   ./scripts/restore-production-db.sh 2025-10-13-23-00
   ```

### Security Breach Detected

**Severity**: P0 (Critical)

**Immediate Actions** (DO NOT DELAY):

1. **Isolate affected systems**
   ```bash
   # Block all traffic
   kubectl patch ingress legal-ai-ingress -n production \
     --type='json' -p='[{"op": "replace", "path": "/spec/rules", "value":[]}]'
   ```

2. **Revoke all active sessions**
   ```bash
   # Flush Redis (sessions)
   kubectl exec -it redis-0 -n production -- redis-cli FLUSHALL
   ```

3. **Rotate all secrets**
   ```bash
   # Rotate database passwords
   ./scripts/rotate-db-password.sh

   # Rotate API keys
   ./scripts/rotate-api-keys.sh

   # Rotate JWT secrets
   ./scripts/rotate-jwt-secret.sh
   ```

4. **Contact security team immediately**
   - Email: security@legal-ai-system.com
   - Phone: On-call security engineer
   - Slack: #security-incidents

5. **Preserve evidence**
   ```bash
   # Capture logs
   kubectl logs -n production --all-containers --since=24h > incident-logs.txt

   # Capture database state
   pg_dump $DATABASE_URL > incident-db-dump.sql
   ```

---

## Deployment Checklist Summary

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Database migration tested
- [ ] Backup completed
- [ ] Rollback plan ready
- [ ] Stakeholders notified

### Deployment
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Deploy to production (blue-green)
- [ ] Run smoke tests on production
- [ ] Monitor metrics for 30 minutes

### Post-Deployment
- [ ] Verify all features working
- [ ] Check error rates < 0.1%
- [ ] Check latency < 500ms P95
- [ ] Update documentation
- [ ] Notify stakeholders of completion
- [ ] Close deployment ticket

### Rollback (if needed)
- [ ] Switch traffic back to blue
- [ ] Verify service restored
- [ ] Investigate root cause
- [ ] Create hotfix if needed
- [ ] Document incident

---

## Contact Information

### On-Call Rotation
- **Primary**: Check PagerDuty schedule
- **Secondary**: Check PagerDuty schedule
- **Manager**: manager@legal-ai-system.com

### Escalation
1. On-call engineer (immediate)
2. Team lead (15 min no response)
3. Engineering manager (30 min no response)
4. CTO (1 hour no response)

### External Contacts
- **AWS Support**: 1-800-AWS-SUPPORT
- **Database Support**: support@postgresql.org
- **Security Incidents**: security@legal-ai-system.com

---

**Last Updated**: 2025-10-14
**Next Review**: 2025-11-14
**Owner**: DevOps Team
