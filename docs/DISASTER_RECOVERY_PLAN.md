# Disaster Recovery Plan
## Legal AI System - Business Continuity and Data Protection

**Version**: 1.0
**Last Updated**: 2024-01-15
**Review Frequency**: Quarterly

---

## Table of Contents

1. [Overview](#overview)
2. [Disaster Scenarios](#disaster-scenarios)
3. [Recovery Objectives](#recovery-objectives)
4. [Backup Strategy](#backup-strategy)
5. [Recovery Procedures](#recovery-procedures)
6. [Incident Response](#incident-response)
7. [Testing and Validation](#testing-and-validation)
8. [Roles and Responsibilities](#roles-and-responsibilities)

---

## Overview

### Purpose

This Disaster Recovery (DR) Plan ensures the Legal AI System can recover from catastrophic failures, maintain business continuity, and protect client data in compliance with legal and regulatory requirements.

### Scope

This plan covers:
- **Database systems** (PostgreSQL)
- **Application servers** (FastAPI/Next.js)
- **File storage** (documents, uploads)
- **Cache systems** (Redis)
- **Configuration and secrets**
- **Infrastructure** (Kubernetes clusters)

### Compliance Requirements

- **GDPR Article 32**: Security of processing (backup and recovery)
- **CCPA Section 1798.150**: Data breach liability
- **SOC 2 Type II**: Availability and processing integrity
- **ISO 27001**: Business continuity management

---

## Disaster Scenarios

### Tier 1: Critical (RTO: 1 hour, RPO: 15 minutes)

1. **Database Failure**
   - Primary database server crash
   - Database corruption
   - Accidental data deletion

2. **Complete Data Center Outage**
   - Power failure
   - Network outage
   - Natural disaster

3. **Security Breach**
   - Ransomware attack
   - Data exfiltration
   - Unauthorized access

### Tier 2: High (RTO: 4 hours, RPO: 1 hour)

4. **Application Server Failure**
   - Server crash
   - Container orchestration failure
   - Application bugs causing data loss

5. **Storage System Failure**
   - File storage corruption
   - Object storage unavailability
   - Disk failures

### Tier 3: Medium (RTO: 24 hours, RPO: 4 hours)

6. **Partial Service Degradation**
   - Cache system failure (Redis)
   - Background job processor failure
   - CDN failure

7. **Human Error**
   - Accidental configuration changes
   - Code deployment errors
   - Operational mistakes

---

## Recovery Objectives

### RTO (Recovery Time Objective)

Maximum acceptable downtime:

| Service | RTO | Priority |
|---------|-----|----------|
| Database | 1 hour | Critical |
| API Backend | 1 hour | Critical |
| Web Frontend | 2 hours | High |
| File Storage | 4 hours | High |
| Redis Cache | 4 hours | Medium |
| Background Jobs | 24 hours | Low |

### RPO (Recovery Point Objective)

Maximum acceptable data loss:

| Data Type | RPO | Backup Frequency |
|-----------|-----|------------------|
| Database (transactional) | 15 minutes | Continuous (WAL archiving) |
| Database (full) | 1 day | Daily at 2 AM |
| User Documents | 6 hours | Every 6 hours |
| Redis Cache | 6 hours | Every 6 hours |
| Application Logs | 1 day | Daily |
| Configuration | 0 (version controlled) | Git commits |

---

## Backup Strategy

### Backup Types

#### 1. Database Backups

**Full Backups** (Daily):
```bash
# Location: /var/backups/legal-ai/
# Schedule: 2:00 AM UTC daily
# Retention: 30 days local, 90 days S3
# Format: pg_dump custom format, compressed

/infrastructure/backup/backup_restore.sh backup full
```

**Incremental Backups** (Hourly):
```bash
# Schedule: Every hour during business hours (8 AM - 6 PM weekdays)
# Retention: 7 days

/infrastructure/backup/backup_restore.sh backup incremental
```

**WAL Archiving** (Continuous):
```bash
# Point-in-time recovery capability
# Retention: 7 days
# Location: /var/backups/legal-ai/wal_archive/

# Enable with:
/infrastructure/backup/backup_restore.sh enable-pitr
```

#### 2. File Storage Backups

**User Documents**:
```bash
# Schedule: Every 6 hours
# Retention: 90 days
# Format: tar.gz

tar -czf files_backup.tar.gz /var/lib/legal-ai/storage/
```

**S3 Versioning**:
- Enabled on all S3 buckets
- 30-day version retention
- Lifecycle policies for archival

#### 3. Configuration Backups

**Git-Based**:
- All configuration in Git repositories
- Tagged releases
- Encrypted secrets in separate vault

**Infrastructure as Code**:
- Terraform state in S3 with versioning
- Kubernetes manifests in Git
- Deployment scripts versioned

#### 4. Redis Backups

**RDB Snapshots**:
```bash
# Schedule: Every 6 hours
# Retention: 7 days

redis-cli SAVE
cp /var/lib/redis/dump.rdb /var/backups/legal-ai/redis_$(date +%Y%m%d_%H%M).rdb
```

### Backup Locations

**Primary** (Production Site):
- Local disk: `/var/backups/legal-ai/`
- Fast recovery for recent backups
- 30-day retention

**Secondary** (S3 - Same Region):
- S3 bucket: `s3://legal-ai-backups/`
- Standard-IA storage class
- 90-day retention
- Lifecycle transition to Glacier after 30 days

**Tertiary** (S3 - Different Region):
- S3 bucket: `s3://legal-ai-backups-dr/`
- Cross-region replication
- 365-day retention
- Geographic disaster protection

### Backup Encryption

All backups are encrypted:
- **In Transit**: TLS 1.2+ for transfers
- **At Rest**: AES-256 encryption
- **Key Management**: AWS KMS with key rotation

---

## Recovery Procedures

### Procedure 1: Database Recovery

#### Complete Database Loss

```bash
# 1. Identify latest backup
cd /var/backups/legal-ai
ls -lt legal_ai_full_*.sql.gz | head -1

# 2. Restore database
./backup_restore.sh restore legal_ai_full_20240115_020000.sql.gz

# 3. Apply WAL logs for point-in-time recovery
# (if WAL archiving enabled)
pg_restore_wal.sh 2024-01-15 14:30:00

# 4. Verify data integrity
psql -d legal_ai -c "SELECT COUNT(*) FROM users;"
psql -d legal_ai -c "SELECT COUNT(*) FROM documents;"

# 5. Restart application
kubectl rollout restart deployment/legal-ai-api
```

**Estimated Time**: 30-60 minutes

#### Point-in-Time Recovery

```bash
# Restore to specific timestamp (requires WAL archiving)
./point_in_time_recovery.sh "2024-01-15 14:30:00"
```

**Estimated Time**: 45-90 minutes

### Procedure 2: Complete System Recovery

#### Scenario: Total Infrastructure Loss

**Prerequisites**:
- Access to S3 backups
- Fresh Kubernetes cluster
- DNS control

**Steps**:

```bash
# 1. Provision new infrastructure
cd infrastructure/terraform
terraform apply

# 2. Deploy Kubernetes cluster
cd ../kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f configmaps/
kubectl apply -f secrets/

# 3. Restore database
# Download latest backup from S3
aws s3 cp s3://legal-ai-backups/latest_full.sql.gz ./
./backup_restore.sh restore latest_full.sql.gz

# 4. Restore file storage
aws s3 sync s3://legal-ai-storage/ /var/lib/legal-ai/storage/

# 5. Deploy applications
kubectl apply -f deployments/
kubectl apply -f services/
kubectl apply -f ingress.yaml

# 6. Verify services
kubectl get pods
kubectl get services
curl https://api.legal-ai.example.com/health

# 7. Update DNS (if needed)
# Point DNS to new load balancer IP

# 8. Test critical workflows
./tests/smoke_tests.sh
```

**Estimated Time**: 2-4 hours

### Procedure 3: File Storage Recovery

```bash
# 1. Stop application (prevent writes)
kubectl scale deployment/legal-ai-api --replicas=0

# 2. Restore files from backup
tar -xzf /var/backups/legal-ai/files_20240115_080000.tar.gz -C /

# Or restore from S3
aws s3 sync s3://legal-ai-backups/files/ /var/lib/legal-ai/storage/

# 3. Verify file integrity
find /var/lib/legal-ai/storage -type f | wc -l
du -sh /var/lib/legal-ai/storage

# 4. Restart application
kubectl scale deployment/legal-ai-api --replicas=3
```

**Estimated Time**: 1-2 hours (depending on data size)

### Procedure 4: Configuration Recovery

```bash
# 1. Clone configuration repository
git clone https://github.com/legal-ai/infrastructure.git
cd infrastructure

# 2. Checkout specific version (if needed)
git checkout tags/v1.2.3

# 3. Restore secrets from vault
./scripts/restore_secrets.sh

# 4. Apply configuration
kubectl apply -f kubernetes/

# 5. Verify
kubectl get configmaps
kubectl get secrets
```

**Estimated Time**: 15-30 minutes

---

## Incident Response

### Incident Classification

| Level | Description | Response Time | Escalation |
|-------|-------------|---------------|------------|
| P0 | Complete service outage | 15 minutes | CEO, CTO |
| P1 | Partial service outage | 1 hour | CTO, Engineering Lead |
| P2 | Service degradation | 4 hours | Engineering Lead |
| P3 | Minor issues | 24 hours | On-call engineer |

### Response Workflow

```
1. DETECT
   └─> Monitoring alerts triggered
   └─> Manual discovery

2. ASSESS
   └─> Determine severity (P0-P3)
   └─> Identify affected systems
   └─> Estimate impact (users, data, revenue)

3. ESCALATE
   └─> Notify on-call engineer
   └─> Escalate per severity level
   └─> Create incident ticket

4. RESPOND
   └─> Activate disaster recovery plan
   └─> Execute recovery procedures
   └─> Communicate with stakeholders

5. RECOVER
   └─> Restore services
   └─> Verify functionality
   └─> Monitor stability

6. REVIEW
   └─> Post-incident review (PIR)
   └─> Document lessons learned
   └─> Update procedures
```

### Communication Plan

**Internal**:
- Slack channel: `#incidents`
- Email: `incidents@legal-ai.com`
- Phone tree for P0/P1

**External**:
- Status page: `status.legal-ai.com`
- Customer email notifications
- Social media updates (if major)

---

## Testing and Validation

### Backup Verification

**Daily**:
```bash
# Automated integrity checks
for backup in /var/backups/legal-ai/legal_ai_full_*.sql.gz; do
    sha256sum -c "${backup}.sha256" || alert "Backup integrity failed: $backup"
done
```

**Weekly**:
```bash
# List backup contents
./backup_restore.sh list
./backup_restore.sh verify latest_backup.sql.gz
```

**Monthly**:
```bash
# Automated DR test (first Sunday)
# Restores latest backup to test database
./backup_restore.sh test-dr
```

### Recovery Testing Schedule

| Test Type | Frequency | Last Performed | Next Scheduled |
|-----------|-----------|----------------|----------------|
| Backup verification | Daily | 2024-01-15 | 2024-01-16 |
| Database restore | Monthly | 2024-01-07 | 2024-02-04 |
| Full system recovery | Quarterly | 2023-12-15 | 2024-03-15 |
| Tabletop exercise | Semi-annually | 2023-11-01 | 2024-05-01 |
| Full DR drill | Annually | 2023-06-15 | 2024-06-15 |

### Test Procedures

**Monthly Database Restore Test**:
```bash
# Automated via cron on first Sunday of month
0 4 1-7 * 0 root /infrastructure/backup/backup_restore.sh test-dr >> /var/log/legal-ai/dr_test.log 2>&1
```

**Quarterly Full Recovery Test**:
1. Provision test environment
2. Restore all backups
3. Verify all services
4. Test critical user workflows
5. Document results
6. Update procedures if needed

**Test Acceptance Criteria**:
- All backups restore successfully
- No data loss detected
- RTO objectives met
- All critical features functional
- Documentation accurate and complete

---

## Roles and Responsibilities

### Incident Response Team

**Incident Commander** (CTO):
- Overall incident response coordination
- Communication with executives
- Final decision authority

**Technical Lead** (Principal Engineer):
- Execute recovery procedures
- Coordinate technical team
- Provide status updates

**Database Administrator**:
- Database restoration
- Data integrity verification
- Performance optimization post-recovery

**DevOps Engineer**:
- Infrastructure provisioning
- Service deployment
- Monitoring and alerting

**Security Lead**:
- Security incident assessment
- Access control during recovery
- Post-incident security review

**Communications Lead**:
- Internal communications
- Customer notifications
- Status page updates

### On-Call Rotation

| Week | Primary | Secondary | Database |
|------|---------|-----------|----------|
| Jan 15-21 | Engineer A | Engineer B | DBA 1 |
| Jan 22-28 | Engineer C | Engineer D | DBA 2 |
| Jan 29-Feb 4 | Engineer E | Engineer F | DBA 1 |

**On-Call Responsibilities**:
- Monitor alerts 24/7
- Respond within SLA
- Execute recovery procedures
- Escalate as needed
- Document incidents

---

## Appendices

### Appendix A: Contact Information

**Emergency Contacts**:
```
CEO: +1-555-0100 (ceo@legal-ai.com)
CTO: +1-555-0101 (cto@legal-ai.com)
Principal Engineer: +1-555-0102
On-Call: +1-555-0199 (pagerduty)
```

**Vendor Support**:
```
AWS Support: 1-866-321-2211 (Enterprise)
Database Support: support@postgresql.com
DNS Provider: support@cloudflare.com
```

### Appendix B: Backup Inventory

**Current Backup Status** (as of 2024-01-15):

| Backup Type | Size | Location | Last Backup | Status |
|-------------|------|----------|-------------|--------|
| Full Database | 15 GB | Local + S3 | 2024-01-15 02:00 | ✓ |
| WAL Archive | 2 GB | Local + S3 | 2024-01-15 14:00 | ✓ |
| File Storage | 50 GB | S3 | 2024-01-15 08:00 | ✓ |
| Redis | 500 MB | Local | 2024-01-15 12:00 | ✓ |
| Configuration | 10 MB | Git | 2024-01-15 10:30 | ✓ |

### Appendix C: Recovery Time Log

Document actual recovery times for continuous improvement:

| Date | Incident | Type | RTO Target | Actual | Notes |
|------|----------|------|------------|--------|-------|
| 2024-01-10 | DB corruption | P1 | 1 hour | 45 min | WAL recovery worked well |
| 2023-12-15 | Full DR test | Test | 4 hours | 3.5 hours | Met objectives |

### Appendix D: Useful Commands

**Quick Reference**:

```bash
# List backups
ls -lh /var/backups/legal-ai/

# Restore latest database backup
latest=$(ls -t /var/backups/legal-ai/legal_ai_full_*.sql.gz | head -1)
./backup_restore.sh restore $latest

# Check database size
psql -d legal_ai -c "SELECT pg_size_pretty(pg_database_size('legal_ai'));"

# Verify application health
curl https://api.legal-ai.example.com/health/detailed

# Check Kubernetes pods
kubectl get pods -n legal-ai

# View recent logs
kubectl logs -n legal-ai deployment/legal-ai-api --tail=100
```

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-15 | DevOps Team | Initial version |

**Next Review Date**: 2024-04-15
**Document Owner**: CTO
**Classification**: Internal - Confidential

---

**This is a living document. Update after each incident and review quarterly.**
