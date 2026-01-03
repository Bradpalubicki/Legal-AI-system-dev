# Production Logging Configuration Guide

**Status:** ✅ Configured
**Priority:** Critical (Production)
**Last Updated:** 2025-10-14

## Overview

The Legal AI System has a comprehensive logging infrastructure designed for production environments with structured JSON logging, specialized audit trails, and environment-aware configuration.

## Current Logging Infrastructure

### Architecture

Location: `backend/app/src/core/logging.py`

**Key Components:**
1. **CustomJSONFormatter** - Structured JSON logging with automatic context
2. **RequestContextLogger** - Request ID tracking for distributed tracing
3. **AuditLogger** - Legal compliance and audit trail logging
4. **SecurityLogger** - Security events and authentication tracking
5. **PerformanceLogger** - Performance metrics and slow query detection

### Log Files

Default log directory: `backend/logs/`

| Log File | Purpose | Rotation | Retention |
|----------|---------|----------|-----------|
| `app.log` | General application logs | 50MB | 10 backups |
| `error.log` | ERROR and CRITICAL only | 50MB | 20 backups |
| `audit.log` | Audit trail (immutable) | 100MB | 50 backups |
| `security.log` | Security events | 100MB | 30 backups |

### Log Formats

**JSON Format (Production Recommended):**
```json
{
  "timestamp": "2025-10-14T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "legal-ai-system",
  "application": "legal-ai-system",
  "environment": "production",
  "message": "Document analyzed successfully",
  "request_id": "req_abc123",
  "user_id": "user_xyz789",
  "document_id": "doc_456",
  "duration_ms": 1250
}
```

**Detailed Format (Development):**
```
2025-10-14 10:30:45,123 - legal-ai-system - INFO - [req_abc123] Document analyzed successfully
```

## Production Configuration

### Environment Variables

Add to `.env`:

```bash
# =============================================================================
# PRODUCTION LOGGING CONFIGURATION
# =============================================================================

# Log Level: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Production: INFO or WARNING
# Staging: INFO
# Development: DEBUG
LOG_LEVEL=INFO

# Log Format: json or detailed
# Production: json (for log aggregation)
# Development: detailed (human-readable)
LOG_FORMAT=json

# Log Directory (optional - defaults to backend/logs)
LOG_DIR=/var/log/legal-ai-system

# Enable specific loggers
ENABLE_AUDIT_LOGGING=true
ENABLE_SECURITY_LOGGING=true
ENABLE_PERFORMANCE_LOGGING=true

# Performance Logging Thresholds
SLOW_QUERY_THRESHOLD_MS=1000
SLOW_REQUEST_THRESHOLD_MS=2000

# Log Retention (days)
LOG_RETENTION_DAYS=90
AUDIT_LOG_RETENTION_DAYS=2555  # 7 years for legal compliance
```

### Recommended Log Levels by Environment

#### Production
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json

# Library log levels (reduce noise)
UVICORN_LOG_LEVEL=WARNING
SQLALCHEMY_LOG_LEVEL=WARNING
HTTPX_LOG_LEVEL=WARNING
```

**What Gets Logged:**
- ✅ INFO: API requests, business logic, successful operations
- ✅ WARNING: Recoverable errors, deprecation warnings
- ✅ ERROR: Application errors, failed operations
- ✅ CRITICAL: System failures, data corruption
- ❌ DEBUG: Not logged (too verbose)

#### Staging
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
UVICORN_LOG_LEVEL=INFO
SQLALCHEMY_LOG_LEVEL=INFO  # Log SQL queries for debugging
```

#### Development
```bash
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed
UVICORN_LOG_LEVEL=DEBUG
SQLALCHEMY_LOG_LEVEL=INFO
```

**What Gets Logged:**
- ✅ All levels including DEBUG
- ✅ SQL queries (helpful for optimization)
- ✅ Request/response bodies (if needed)

## Specialized Loggers

### 1. Audit Logger

**Purpose:** Track all user actions for legal compliance and audit trails

**Usage:**
```python
from app.src.core.logging import AuditLogger

audit_logger = AuditLogger()

# Log user action
audit_logger.log_action(
    action="document_upload",
    resource="document",
    resource_id="doc_123",
    user_id="user_456",
    details={"filename": "contract.pdf", "size_bytes": 1024000},
    ip_address=request.client.host,
    success=True
)

# Log data access (HIPAA/GDPR compliance)
audit_logger.log_data_access(
    user_id="user_789",
    data_type="client_record",
    data_id="client_123",
    action="read",
    ip_address="192.168.1.1"
)

# Log security event
audit_logger.log_security_event(
    event_type="login_success",
    user_id="user_456",
    ip_address="192.168.1.1",
    details={"mfa_used": True}
)
```

**Output Example:**
```json
{
  "timestamp": "2025-10-14T10:30:45.123456+00:00",
  "level": "INFO",
  "logger": "legal-ai-system.audit",
  "audit_action": "document_upload",
  "audit_resource": "document",
  "audit_resource_id": "doc_123",
  "audit_user_id": "user_456",
  "audit_ip_address": "192.168.1.1",
  "audit_success": true,
  "audit_details": {"filename": "contract.pdf", "size_bytes": 1024000}
}
```

**Retention:** 7 years minimum (legal compliance requirement)

### 2. Security Logger

**Purpose:** Track authentication, authorization, and security events

**Usage:**
```python
from app.src.core.logging import SecurityLogger

security_logger = SecurityLogger()

# Log authentication attempt
security_logger.log_auth_attempt(
    username="user@example.com",
    success=True,
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    mfa_used=True
)

# Log authorization failure
security_logger.log_permission_denied(
    user_id="user_123",
    resource="document",
    resource_id="doc_456",
    required_permission="document:delete",
    ip_address="192.168.1.1"
)

# Log suspicious activity
security_logger.log_suspicious_activity(
    activity_type="rate_limit_exceeded",
    user_id="user_123",
    ip_address="192.168.1.1",
    details={"requests_per_minute": 150, "threshold": 60}
)
```

**Critical Security Events to Log:**
- ✅ Login attempts (success and failure)
- ✅ Password changes
- ✅ MFA enrollment/changes
- ✅ Permission denials
- ✅ Rate limit violations
- ✅ API key usage
- ✅ Suspicious patterns (brute force, SQL injection attempts)

### 3. Performance Logger

**Purpose:** Track performance metrics, slow queries, and bottlenecks

**Usage:**
```python
from app.src.core.logging import PerformanceLogger

perf_logger = PerformanceLogger()

# Log slow query
perf_logger.log_slow_query(
    query="SELECT * FROM documents WHERE ...",
    duration_ms=2500,
    threshold_ms=1000,
    params={"user_id": "user_123"}
)

# Log slow request
perf_logger.log_slow_request(
    method="POST",
    path="/api/documents/analyze",
    duration_ms=5000,
    threshold_ms=2000,
    status_code=200
)

# Log cache performance
perf_logger.log_cache_stats(
    cache_name="document_cache",
    hits=850,
    misses=150,
    hit_rate=0.85,
    size_mb=512
)
```

**Performance Metrics Tracked:**
- Request duration (P50, P95, P99)
- Database query duration
- Cache hit rates
- AI API call duration
- Document processing time
- Background job duration

### 4. Request Context Logger

**Purpose:** Automatic request ID tracking for distributed tracing

**Features:**
- Automatic request ID generation (`req_` prefix)
- Request ID propagation across services
- Correlation of all logs within a request

**Automatic Context:**
```python
# Automatically adds to all logs within a request:
{
  "request_id": "req_abc123xyz",
  "user_id": "user_456",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "method": "POST",
  "path": "/api/documents/analyze"
}
```

**Manual Usage:**
```python
from app.src.core.logging import RequestContextLogger

logger = RequestContextLogger(__name__)

# Logs automatically include request context
logger.info("Processing document", extra={"document_id": "doc_123"})
```

## Log Aggregation & Analysis

### Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)

**Recommended for:** Medium to large deployments

**Setup:**

1. **Install ELK Stack:**
```bash
# Using Docker Compose
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - /var/log/legal-ai-system:/var/log/legal-ai-system:ro
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

2. **Logstash Pipeline Configuration:**
```ruby
# logstash/pipeline/legal-ai.conf
input {
  file {
    path => "/var/log/legal-ai-system/app.log"
    codec => json
    type => "application"
  }
  file {
    path => "/var/log/legal-ai-system/audit.log"
    codec => json
    type => "audit"
  }
  file {
    path => "/var/log/legal-ai-system/security.log"
    codec => json
    type => "security"
  }
}

filter {
  # Add geo-location for IP addresses
  if [ip_address] {
    geoip {
      source => "ip_address"
    }
  }

  # Parse duration strings
  if [duration_ms] {
    mutate {
      convert => { "duration_ms" => "integer" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "legal-ai-%{type}-%{+YYYY.MM.dd}"
    user => "elastic"
    password => "${ELASTIC_PASSWORD}"
  }
}
```

3. **Kibana Dashboards:**
- **Overview Dashboard**: Request volume, error rates, response times
- **Audit Dashboard**: User actions, data access, compliance tracking
- **Security Dashboard**: Auth attempts, permission denials, suspicious activity
- **Performance Dashboard**: Slow queries, API latency, cache hit rates

### Option 2: AWS CloudWatch

**Recommended for:** AWS deployments

**Setup:**

1. **Install CloudWatch Agent:**
```bash
# On EC2 or ECS
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

2. **CloudWatch Agent Configuration:**
```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/legal-ai-system/app.log",
            "log_group_name": "/aws/legal-ai-system/application",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/legal-ai-system/audit.log",
            "log_group_name": "/aws/legal-ai-system/audit",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
```

3. **CloudWatch Insights Queries:**

**Query: Error Rate by Endpoint**
```
fields @timestamp, path, level, message
| filter level = "ERROR"
| stats count() by path
| sort count desc
```

**Query: Slow Requests (>2 seconds)**
```
fields @timestamp, method, path, duration_ms, user_id
| filter duration_ms > 2000
| sort duration_ms desc
```

**Query: Failed Login Attempts**
```
fields @timestamp, audit_action, audit_user_id, audit_ip_address
| filter audit_action = "login_failed"
| stats count() by audit_ip_address
| sort count desc
```

### Option 3: Grafana Loki

**Recommended for:** Kubernetes deployments, cost-conscious teams

**Setup:**

1. **Loki Configuration:**
```yaml
# loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h
```

2. **Promtail Configuration (Log Shipper):**
```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: legal-ai-system
    static_configs:
      - targets:
          - localhost
        labels:
          job: legal-ai-application
          __path__: /var/log/legal-ai-system/*.log
```

3. **Grafana Dashboard:**
```json
{
  "dashboard": {
    "title": "Legal AI System Logs",
    "panels": [
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate({job=\"legal-ai-application\"} |= \"ERROR\" [5m])"
          }
        ]
      },
      {
        "title": "Request Volume",
        "targets": [
          {
            "expr": "rate({job=\"legal-ai-application\"} [1m])"
          }
        ]
      }
    ]
  }
}
```

## Monitoring & Alerting

### Critical Alerts

Set up alerts for these conditions:

#### 1. High Error Rate
```yaml
alert: HighErrorRate
expr: (rate(log_messages{level="ERROR"}[5m]) / rate(log_messages[5m])) > 0.05
for: 5m
labels:
  severity: critical
annotations:
  summary: "Error rate above 5% for 5 minutes"
  description: "Current error rate: {{ $value | humanizePercentage }}"
```

#### 2. Authentication Failures
```yaml
alert: MultipleLoginFailures
expr: sum(rate(log_messages{audit_action="login_failed"}[5m])) > 10
for: 2m
labels:
  severity: warning
annotations:
  summary: "High number of failed login attempts"
  description: "{{ $value }} failed logins per second"
```

#### 3. Slow Request Performance
```yaml
alert: SlowAPIRequests
expr: histogram_quantile(0.95, rate(http_request_duration_ms[5m])) > 5000
for: 10m
labels:
  severity: warning
annotations:
  summary: "95th percentile latency above 5 seconds"
```

#### 4. Disk Space for Logs
```yaml
alert: LogDiskSpaceLow
expr: (node_filesystem_avail_bytes{mountpoint="/var/log"} / node_filesystem_size_bytes) < 0.1
for: 5m
labels:
  severity: critical
annotations:
  summary: "Log partition has less than 10% free space"
```

### Alert Channels

**PagerDuty Integration:**
```python
# app/src/core/alerting.py
import requests

def send_pagerduty_alert(severity, message, details):
    payload = {
        "routing_key": os.getenv("PAGERDUTY_ROUTING_KEY"),
        "event_action": "trigger",
        "payload": {
            "summary": message,
            "severity": severity,  # critical, error, warning, info
            "source": "legal-ai-system",
            "custom_details": details
        }
    }
    requests.post("https://events.pagerduty.com/v2/enqueue", json=payload)

# Usage in code
if error_rate > 0.05:
    logger.critical("High error rate detected", extra={"error_rate": error_rate})
    send_pagerduty_alert("critical", "High error rate", {"rate": error_rate})
```

**Slack Integration:**
```python
def send_slack_alert(channel, message, severity="warning"):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    color = {"critical": "danger", "warning": "warning", "info": "good"}[severity]

    payload = {
        "channel": channel,
        "username": "Legal AI Alerts",
        "icon_emoji": ":warning:",
        "attachments": [{
            "color": color,
            "title": f"{severity.upper()}: Legal AI System Alert",
            "text": message,
            "timestamp": int(time.time())
        }]
    }
    requests.post(webhook_url, json=payload)
```

## Log Retention & Compliance

### Retention Policies

| Log Type | Retention Period | Reason |
|----------|-----------------|--------|
| **Audit Logs** | 7 years | Legal compliance (attorney-client privilege) |
| **Security Logs** | 2 years | Security incident investigation |
| **Application Logs** | 90 days | Debugging and troubleshooting |
| **Error Logs** | 1 year | Pattern analysis and bug tracking |
| **Performance Logs** | 30 days | Performance optimization |

### Automated Cleanup

**Cron Job for Log Rotation:**
```bash
# /etc/cron.daily/legal-ai-log-cleanup
#!/bin/bash

LOG_DIR="/var/log/legal-ai-system"

# Archive old logs
find "$LOG_DIR/app.log.*" -mtime +90 -exec gzip {} \;
find "$LOG_DIR/error.log.*" -mtime +365 -exec gzip {} \;

# Delete ancient logs (keep audit logs forever)
find "$LOG_DIR/app.log.*" -mtime +180 -delete
find "$LOG_DIR/error.log.*" -mtime +730 -delete
find "$LOG_DIR/security.log.*" -mtime +730 -delete

# Never delete audit logs automatically (manual archival only)
# Audit logs are archived to cold storage after 7 years
```

**Logrotate Configuration:**
```
# /etc/logrotate.d/legal-ai-system
/var/log/legal-ai-system/app.log {
    daily
    rotate 90
    compress
    delaycompress
    missingok
    notifempty
    create 0644 legal-ai legal-ai
}

/var/log/legal-ai-system/error.log {
    daily
    rotate 365
    compress
    delaycompress
    missingok
    notifempty
    create 0644 legal-ai legal-ai
}

/var/log/legal-ai-system/audit.log {
    daily
    rotate 2555  # 7 years
    compress
    delaycompress
    missingok
    notifempty
    create 0644 legal-ai legal-ai
    # Never delete, only rotate
    maxage 0
}
```

### Cold Storage Archival

For long-term audit log retention:

**S3 Glacier Integration:**
```python
# scripts/archive_old_audit_logs.py
import boto3
from datetime import datetime, timedelta

s3 = boto3.client('s3')

def archive_old_audit_logs():
    """Archive audit logs older than 90 days to S3 Glacier"""
    cutoff_date = datetime.now() - timedelta(days=90)

    for log_file in glob.glob("/var/log/legal-ai-system/audit.log.*"):
        file_date = datetime.fromtimestamp(os.path.getmtime(log_file))

        if file_date < cutoff_date:
            # Upload to S3 with Glacier storage class
            with open(log_file, 'rb') as f:
                s3.upload_fileobj(
                    f,
                    'legal-ai-audit-archive',
                    f'audit-logs/{os.path.basename(log_file)}',
                    ExtraArgs={'StorageClass': 'GLACIER'}
                )

            # Verify upload before deleting
            # ...
            os.remove(log_file)
            print(f"Archived and removed: {log_file}")

if __name__ == "__main__":
    archive_old_audit_logs()
```

## Security Best Practices

### 1. PII Filtering

**Automatic PII Redaction:**
```python
# app/src/core/logging.py (add to CustomJSONFormatter)

import re

class CustomJSONFormatter(jsonlogger.JsonFormatter):
    PII_PATTERNS = {
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
        'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
    }

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Redact PII from message
        if 'message' in log_record:
            message = log_record['message']
            for pii_type, pattern in self.PII_PATTERNS.items():
                message = pattern.sub(f'[REDACTED_{pii_type.upper()}]', message)
            log_record['message'] = message
```

### 2. Sensitive Field Filtering

**Never Log These Fields:**
```python
SENSITIVE_FIELDS = [
    'password', 'token', 'api_key', 'secret', 'private_key',
    'ssn', 'social_security', 'credit_card', 'cvv', 'pin',
    'session_id', 'csrf_token', 'oauth_token'
]

def sanitize_log_data(data: dict) -> dict:
    """Remove sensitive fields from log data"""
    sanitized = data.copy()
    for field in SENSITIVE_FIELDS:
        if field in sanitized:
            sanitized[field] = '[REDACTED]'
    return sanitized

# Usage
logger.info("User profile updated", extra=sanitize_log_data(user_data))
```

### 3. Log Access Control

**File Permissions:**
```bash
# Only legal-ai user and root can read logs
chown legal-ai:legal-ai /var/log/legal-ai-system/*.log
chmod 640 /var/log/legal-ai-system/*.log

# Audit logs are even more restricted
chmod 600 /var/log/legal-ai-system/audit.log
```

**Database Audit Logging:**
```sql
-- PostgreSQL audit logging
CREATE TABLE audit_log_access (
    id SERIAL PRIMARY KEY,
    accessed_at TIMESTAMP DEFAULT NOW(),
    accessed_by VARCHAR(255),
    log_type VARCHAR(50),
    reason TEXT,
    ip_address INET
);

-- Log every audit log access
CREATE TRIGGER log_audit_access
BEFORE SELECT ON audit_logs
FOR EACH STATEMENT
EXECUTE FUNCTION record_audit_access();
```

## Performance Optimization

### 1. Asynchronous Logging

**Non-blocking Log Writes:**
```python
# app/src/core/logging.py
from logging.handlers import QueueHandler, QueueListener
import queue

# Create queue for async logging
log_queue = queue.Queue(-1)  # Unlimited size

# Queue handler (fast, non-blocking)
queue_handler = QueueHandler(log_queue)

# Actual handlers (slow, done in background)
file_handler = RotatingFileHandler('app.log', maxBytes=50*1024*1024, backupCount=10)
console_handler = logging.StreamHandler()

# Listener processes queue in background thread
listener = QueueListener(log_queue, file_handler, console_handler, respect_handler_level=True)
listener.start()

# Add queue handler to logger
logger.addHandler(queue_handler)
```

### 2. Sampling High-Volume Logs

**Sample DEBUG Logs:**
```python
import random

def should_log_debug() -> bool:
    """Only log 10% of DEBUG messages to reduce volume"""
    return random.random() < 0.1

# Usage
if logger.isEnabledFor(logging.DEBUG) and should_log_debug():
    logger.debug("Detailed debug information", extra=large_context)
```

### 3. Lazy Evaluation

**Defer Expensive Operations:**
```python
# Bad - always evaluates, even if DEBUG disabled
logger.debug(f"Full document: {json.dumps(large_document)}")

# Good - only evaluates if DEBUG enabled
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("Full document: %s", json.dumps(large_document))

# Better - lazy string interpolation
logger.debug("Full document: %s", lambda: json.dumps(large_document))
```

## Troubleshooting

### Problem: Logs Not Appearing

**Check:**
1. Verify log directory exists and is writable:
   ```bash
   ls -la /var/log/legal-ai-system/
   sudo chmod 755 /var/log/legal-ai-system
   ```

2. Check LOG_LEVEL environment variable:
   ```bash
   echo $LOG_LEVEL
   # Should be DEBUG, INFO, WARNING, ERROR, or CRITICAL
   ```

3. Verify application is using correct config:
   ```python
   import logging
   logger = logging.getLogger('legal-ai-system')
   print(logger.level)  # Should match LOG_LEVEL
   print(logger.handlers)  # Should show file handlers
   ```

### Problem: Log Files Growing Too Large

**Solutions:**
1. Reduce log level in production (INFO instead of DEBUG)
2. Enable log rotation more frequently
3. Implement sampling for high-volume events
4. Archive old logs to cloud storage

### Problem: Missing Request Context

**Check:**
1. RequestContextLogger is being used:
   ```python
   from app.src.core.logging import RequestContextLogger
   logger = RequestContextLogger(__name__)
   ```

2. Middleware is installed:
   ```python
   # In main.py
   app.add_middleware(RequestLoggingMiddleware)
   ```

### Problem: Logs Missing in Kibana/Loki

**Check:**
1. Log format is valid JSON:
   ```bash
   cat /var/log/legal-ai-system/app.log | jq .
   # Should parse without errors
   ```

2. Logstash/Promtail is running:
   ```bash
   docker ps | grep logstash
   systemctl status promtail
   ```

3. Check shipper logs:
   ```bash
   docker logs logstash
   journalctl -u promtail
   ```

## Testing Logging Configuration

### Manual Testing

**Test Each Log Level:**
```python
# test_logging.py
import logging
from app.src.core.logging import setup_logging, RequestContextLogger

setup_logging()
logger = RequestContextLogger(__name__)

logger.debug("DEBUG: This is a debug message")
logger.info("INFO: This is an info message")
logger.warning("WARNING: This is a warning message")
logger.error("ERROR: This is an error message")
logger.critical("CRITICAL: This is a critical message")
```

**Test Audit Logging:**
```python
from app.src.core.logging import AuditLogger

audit = AuditLogger()
audit.log_action(
    action="test_action",
    resource="test_resource",
    user_id="test_user",
    success=True
)
```

**Test Security Logging:**
```python
from app.src.core.logging import SecurityLogger

security = SecurityLogger()
security.log_auth_attempt(
    username="test@example.com",
    success=True,
    ip_address="127.0.0.1"
)
```

### Automated Testing

**Pytest Test:**
```python
# tests/test_logging.py
import pytest
import logging
import json
from pathlib import Path

def test_logging_produces_json(tmp_path):
    """Test that logs are valid JSON"""
    log_file = tmp_path / "test.log"

    handler = logging.FileHandler(log_file)
    handler.setFormatter(CustomJSONFormatter())

    logger = logging.getLogger("test")
    logger.addHandler(handler)
    logger.info("Test message", extra={"test_field": "test_value"})

    # Read log file
    log_content = log_file.read_text()
    log_data = json.loads(log_content)

    assert log_data["message"] == "Test message"
    assert log_data["test_field"] == "test_value"
    assert "timestamp" in log_data

def test_pii_redaction():
    """Test that PII is redacted from logs"""
    formatter = CustomJSONFormatter()

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User SSN is 123-45-6789",
        args=(),
        exc_info=None
    )

    formatted = json.loads(formatter.format(record))
    assert "123-45-6789" not in formatted["message"]
    assert "[REDACTED_SSN]" in formatted["message"]
```

## Next Steps

After configuring production logging:

1. ✅ Set up log aggregation (ELK/CloudWatch/Loki)
2. ✅ Configure monitoring alerts
3. ✅ Create logging dashboard in Grafana/Kibana
4. ✅ Document log access procedures
5. ✅ Train team on log analysis
6. ✅ Set up automated archival
7. ✅ Test alert channels (PagerDuty/Slack)
8. ✅ Review logs weekly for patterns

---

**Questions?** Check the logging configuration in `backend/app/src/core/logging.py`
**Issues?** Verify environment variables and file permissions
**Need Help?** Review CloudWatch/Kibana/Loki documentation
