# Monitoring & Alerting Configuration Guide

**Status:** ✅ Configured
**Priority:** Critical (Production)
**Last Updated:** 2025-10-14

## Overview

This guide covers the complete monitoring and alerting infrastructure for the Legal AI System, including metrics collection, alert rules, notification channels, and dashboard setup.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Legal AI System                           │
├─────────────┬─────────────┬────────────┬───────────────────┤
│  Backend    │  Frontend   │ PostgreSQL │     Redis         │
│  (FastAPI)  │  (Next.js)  │            │                   │
└──────┬──────┴──────┬──────┴─────┬──────┴──────┬────────────┘
       │             │            │             │
       │ /metrics    │ /metrics   │ :9187       │ :9121
       ▼             ▼            ▼             ▼
┌────────────────────────────────────────────────────────────┐
│              Prometheus (Metrics Collection)                │
│  - Scrapes metrics every 15s                               │
│  - Stores time-series data (90 days retention)             │
│  - Evaluates alert rules every 30s                         │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       │ Alerts Triggered
                       ▼
┌────────────────────────────────────────────────────────────┐
│             Alertmanager (Alert Routing)                    │
│  - Groups related alerts                                   │
│  - Routes to appropriate channels                          │
│  - Prevents alert fatigue with throttling                  │
└──────┬────────┬────────┬─────────┬─────────────────────────┘
       │        │        │         │
       │        │        │         │
       ▼        ▼        ▼         ▼
  PagerDuty  Slack   Email   Webhook
  (Critical) (Warn)  (Info)  (Custom)
```

## Components

### 1. Prometheus
- **Purpose**: Metrics collection, storage, and alerting
- **Port**: 9090
- **Retention**: 90 days
- **Scrape Interval**: 15 seconds

### 2. Alertmanager
- **Purpose**: Alert routing and notification
- **Port**: 9093
- **Features**: Grouping, throttling, silencing

### 3. Grafana
- **Purpose**: Dashboards and visualization
- **Port**: 3001
- **Features**: Pre-built dashboards, alert visualization

### 4. Exporters
- **Node Exporter** (9100): System metrics (CPU, memory, disk)
- **PostgreSQL Exporter** (9187): Database metrics
- **Redis Exporter** (9121): Cache metrics
- **Backend Metrics** (8000/metrics): Application metrics

## Quick Start

### 1. Create Monitoring Stack

Create `docker/monitoring/docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: legal-ai-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/alerts:/etc/prometheus/alerts:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=90d'
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: legal-ai-alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager-data:/alertmanager
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:10.2.2
    container_name: legal-ai-grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - grafana-data:/var/lib/grafana
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:v1.7.0
    container_name: legal-ai-node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/host:ro,rslave
    networks:
      - monitoring

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15.0
    container_name: legal-ai-postgres-exporter
    restart: unless-stopped
    ports:
      - "9187:9187"
    environment:
      DATA_SOURCE_NAME: "postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}"
    networks:
      - monitoring

  redis-exporter:
    image: oliver006/redis_exporter:v1.55.0
    container_name: legal-ai-redis-exporter
    restart: unless-stopped
    ports:
      - "9121:9121"
    environment:
      REDIS_ADDR: "redis:6379"
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus-data:
  alertmanager-data:
  grafana-data:
```

### 2. Start Monitoring Stack

```bash
cd docker/monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Verify all services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 3. Access Dashboards

- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093
- **Grafana**: http://localhost:3001 (admin/your-password)

## Prometheus Configuration

Create `docker/monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 30s
  external_labels:
    cluster: 'legal-ai-production'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'

# Alert rules
rule_files:
  - '/etc/prometheus/alerts/*.yml'

# Scrape configurations
scrape_configs:
  # Legal AI Backend
  - job_name: 'legal-ai-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  # Legal AI Frontend
  - job_name: 'legal-ai-frontend'
    static_configs:
      - targets: ['frontend:3000']
    metrics_path: '/api/metrics'
    scrape_interval: 30s

  # PostgreSQL Database
  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  # Redis Cache
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 15s

  # Node/System Metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 15s

  # Prometheus Self-Monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Alertmanager
  - job_name: 'alertmanager'
    static_configs:
      - targets: ['alertmanager:9093']
```

## Alert Rules

Create `docker/monitoring/prometheus/alerts/critical.yml`:

```yaml
groups:
  - name: critical_alerts
    interval: 30s
    rules:
      # Service Down
      - alert: ServiceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
          category: availability
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.job }} on {{ $labels.instance }} has been down for more than 2 minutes."
          runbook: "https://docs.legal-ai-system.com/runbooks/service-down"

      # High Error Rate
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
            /
            sum(rate(http_requests_total[5m])) by (job)
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          category: errors
        annotations:
          summary: "High error rate on {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
          runbook: "https://docs.legal-ai-system.com/runbooks/high-error-rate"

      # Database Connection Pool Exhausted
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          (
            sum(pg_stat_activity_count) by (instance)
            /
            sum(pg_settings_max_connections) by (instance)
          ) > 0.9
        for: 2m
        labels:
          severity: critical
          category: database
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "{{ $value | humanizePercentage }} of connections in use (threshold: 90%)"
          runbook: "https://docs.legal-ai-system.com/runbooks/db-connections"

      # Disk Space Critical
      - alert: DiskSpaceCritical
        expr: |
          (
            node_filesystem_avail_bytes{mountpoint="/"}
            /
            node_filesystem_size_bytes{mountpoint="/"}
          ) < 0.1
        for: 5m
        labels:
          severity: critical
          category: infrastructure
        annotations:
          summary: "Critical disk space on {{ $labels.instance }}"
          description: "Only {{ $value | humanizePercentage }} disk space remaining"
          runbook: "https://docs.legal-ai-system.com/runbooks/disk-space"

      # Memory Pressure
      - alert: HighMemoryUsage
        expr: |
          (
            1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
          ) > 0.9
        for: 5m
        labels:
          severity: critical
          category: infrastructure
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value | humanizePercentage }}"
          runbook: "https://docs.legal-ai-system.com/runbooks/memory"

      # CPU Saturation
      - alert: HighCPUUsage
        expr: |
          100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
        for: 10m
        labels:
          severity: critical
          category: infrastructure
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value | printf \"%.2f\" }}%"
          runbook: "https://docs.legal-ai-system.com/runbooks/cpu"

      # API Latency P95
      - alert: HighAPILatency
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket[5m])
          ) > 5
        for: 10m
        labels:
          severity: critical
          category: performance
        annotations:
          summary: "High API latency on {{ $labels.job }}"
          description: "95th percentile latency is {{ $value | printf \"%.2f\" }}s (threshold: 5s)"
          runbook: "https://docs.legal-ai-system.com/runbooks/latency"
```

Create `docker/monitoring/prometheus/alerts/warning.yml`:

```yaml
groups:
  - name: warning_alerts
    interval: 60s
    rules:
      # Elevated Error Rate
      - alert: ElevatedErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
            /
            sum(rate(http_requests_total[5m])) by (job)
          ) > 0.01
        for: 10m
        labels:
          severity: warning
          category: errors
        annotations:
          summary: "Elevated error rate on {{ $labels.job }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 1%)"

      # Database Slow Queries
      - alert: DatabaseSlowQueries
        expr: rate(pg_stat_database_tup_returned[5m]) / rate(pg_stat_database_tup_fetched[5m]) < 0.1
        for: 10m
        labels:
          severity: warning
          category: database
        annotations:
          summary: "High number of slow queries"
          description: "Query efficiency is {{ $value | humanizePercentage }}"

      # Redis Memory Usage
      - alert: RedisHighMemory
        expr: |
          (
            redis_memory_used_bytes
            /
            redis_memory_max_bytes
          ) > 0.8
        for: 10m
        labels:
          severity: warning
          category: cache
        annotations:
          summary: "Redis memory usage high"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # High Request Rate
      - alert: HighRequestRate
        expr: rate(http_requests_total[1m]) > 1000
        for: 5m
        labels:
          severity: warning
          category: traffic
        annotations:
          summary: "High request rate on {{ $labels.job }}"
          description: "Request rate is {{ $value | printf \"%.0f\" }} req/s"

      # Certificate Expiring Soon
      - alert: SSLCertificateExpiringSoon
        expr: (ssl_certificate_expiry_seconds - time()) / 86400 < 30
        for: 1h
        labels:
          severity: warning
          category: security
        annotations:
          summary: "SSL certificate expiring soon"
          description: "Certificate expires in {{ $value | printf \"%.0f\" }} days"

      # Failed Login Attempts
      - alert: HighFailedLoginRate
        expr: rate(auth_login_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
          category: security
        annotations:
          summary: "High failed login attempt rate"
          description: "{{ $value | printf \"%.0f\" }} failed logins per second"
```

## Alertmanager Configuration

Create `docker/monitoring/alertmanager/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

  # Slack webhook (for all alerts)
  slack_api_url: '${SLACK_WEBHOOK_URL}'

  # PagerDuty integration key (for critical alerts)
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

# Templates for notifications
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Route alerts to appropriate receivers
route:
  # Default receiver for all alerts
  receiver: 'slack-general'

  # Group alerts by these labels to reduce noise
  group_by: ['alertname', 'cluster', 'service']

  # Wait before sending first notification (collect related alerts)
  group_wait: 30s

  # Wait before sending another notification for the same group
  group_interval: 5m

  # Wait before sending notification about resolved alert
  repeat_interval: 4h

  # Sub-routes for specific alert types
  routes:
    # Critical alerts -> PagerDuty + Slack
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true  # Also send to Slack
      routes:
        - match:
            severity: critical
          receiver: 'slack-critical'

    # Warning alerts -> Slack only
    - match:
        severity: warning
      receiver: 'slack-warnings'

    # Infrastructure alerts -> Ops team
    - match:
        category: infrastructure
      receiver: 'slack-ops'

    # Security alerts -> Security team + Email
    - match:
        category: security
      receiver: 'security-team'

    # Database alerts -> DBA team
    - match:
        category: database
      receiver: 'dba-team'

# Alert receivers (notification channels)
receivers:
  # Default Slack channel
  - name: 'slack-general'
    slack_configs:
      - channel: '#legal-ai-alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
            *Summary:* {{ .Annotations.summary }}
            *Description:* {{ .Annotations.description }}
            *Severity:* {{ .Labels.severity }}
            *Started:* {{ .StartsAt | since }}
          {{ end }}
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'
        send_resolved: true

  # Critical alerts to PagerDuty
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - routing_key: '${PAGERDUTY_ROUTING_KEY}'
        severity: 'critical'
        description: '{{ .GroupLabels.alertname }}: {{ .Annotations.summary }}'
        details:
          summary: '{{ .Annotations.summary }}'
          description: '{{ .Annotations.description }}'
          runbook: '{{ .Annotations.runbook }}'
        links:
          - href: '{{ .Annotations.runbook }}'
            text: 'Runbook'

  # Critical Slack channel
  - name: 'slack-critical'
    slack_configs:
      - channel: '#legal-ai-critical'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
            *Summary:* {{ .Annotations.summary }}
            *Description:* {{ .Annotations.description }}
            *Runbook:* {{ .Annotations.runbook }}
            *Started:* {{ .StartsAt | since }}
          {{ end }}
        color: 'danger'
        send_resolved: true

  # Warning Slack channel
  - name: 'slack-warnings'
    slack_configs:
      - channel: '#legal-ai-warnings'
        title: '⚠️ Warning: {{ .GroupLabels.alertname }}'
        text: '{{ .Annotations.summary }}'
        send_resolved: true

  # Ops team
  - name: 'slack-ops'
    slack_configs:
      - channel: '#legal-ai-ops'
        title: 'Infrastructure Alert: {{ .GroupLabels.alertname }}'
        text: '{{ .Annotations.summary }}'

  # Security team
  - name: 'security-team'
    slack_configs:
      - channel: '#legal-ai-security'
        title: '🔒 Security Alert: {{ .GroupLabels.alertname }}'
        text: '{{ .Annotations.summary }}'
        color: 'warning'
    email_configs:
      - to: 'security@legal-ai-system.com'
        from: 'alerts@legal-ai-system.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: '${SMTP_USERNAME}'
        auth_password: '${SMTP_PASSWORD}'
        subject: 'Security Alert: {{ .GroupLabels.alertname }}'

  # DBA team
  - name: 'dba-team'
    slack_configs:
      - channel: '#legal-ai-database'
        title: '🗄️ Database Alert: {{ .GroupLabels.alertname }}'
        text: '{{ .Annotations.summary }}'

# Inhibition rules (suppress certain alerts when others are firing)
inhibit_rules:
  # Suppress other alerts when service is down
  - source_match:
      severity: 'critical'
      alertname: 'ServiceDown'
    target_match_re:
      severity: 'warning|info'
    equal: ['instance']

  # Suppress API errors when database is down
  - source_match:
      alertname: 'DatabaseDown'
    target_match:
      alertname: 'HighErrorRate'
    equal: ['cluster']
```

## Backend Metrics Integration

Add Prometheus metrics to FastAPI backend:

```python
# backend/requirements.txt
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0
```

```python
# backend/app/api/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI, Response
import time

# Custom metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Currently active HTTP requests'
)

# Document processing metrics
DOCUMENT_PROCESSING_DURATION = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration',
    ['document_type']
)

AI_API_CALLS = Counter(
    'ai_api_calls_total',
    'Total AI API calls',
    ['provider', 'model', 'status']
)

# Authentication metrics
AUTH_LOGIN_ATTEMPTS = Counter(
    'auth_login_attempts_total',
    'Total login attempts',
    ['status']
)

AUTH_LOGIN_FAILURES = Counter(
    'auth_login_failures_total',
    'Failed login attempts',
    ['reason']
)

# Database metrics
DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation']
)

# Cache metrics
CACHE_HITS = Counter('cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('cache_misses_total', 'Cache misses')

def setup_metrics(app: FastAPI):
    """Setup Prometheus metrics for FastAPI"""

    # Automatic instrumentation
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )

    instrumentator.instrument(app)

    @app.get("/metrics")
    async def metrics():
        """Expose Prometheus metrics"""
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        )

    return instrumentator

# Usage in middleware
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track custom metrics for each request"""
    ACTIVE_REQUESTS.inc()
    start_time = time.time()

    try:
        response = await call_next(request)

        # Track request
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        # Track duration
        duration = time.time() - start_time
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response
    finally:
        ACTIVE_REQUESTS.dec()

# Usage in business logic
async def process_document(document):
    """Process document and track metrics"""
    with DOCUMENT_PROCESSING_DURATION.labels(
        document_type=document.type
    ).time():
        # Process document
        result = await analyze_document(document)

    return result

async def call_ai_api(provider, model, prompt):
    """Call AI API and track metrics"""
    try:
        response = await ai_client.complete(model, prompt)
        AI_API_CALLS.labels(
            provider=provider,
            model=model,
            status='success'
        ).inc()
        return response
    except Exception as e:
        AI_API_CALLS.labels(
            provider=provider,
            model=model,
            status='error'
        ).inc()
        raise
```

## Grafana Dashboards

Create `docker/monitoring/grafana/provisioning/datasources/prometheus.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

Create `docker/monitoring/grafana/provisioning/dashboards/default.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'Legal AI System'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

### Pre-built Dashboards

**1. System Overview Dashboard**
- Request rate and error rate
- Response time (P50, P95, P99)
- Active requests
- Service uptime

**2. Infrastructure Dashboard**
- CPU usage
- Memory usage
- Disk I/O
- Network traffic

**3. Database Dashboard**
- Query rate
- Slow queries
- Connection pool usage
- Table sizes

**4. Application Dashboard**
- Document processing rate
- AI API calls
- Authentication metrics
- Cache hit rate

**5. Security Dashboard**
- Failed login attempts
- Permission denials
- Suspicious activity
- API key usage

## Environment Variables

Add to `.env`:

```bash
# =============================================================================
# MONITORING & ALERTING
# =============================================================================

# Enable Prometheus metrics endpoint
ENABLE_METRICS=true

# Grafana Admin
GRAFANA_ADMIN_PASSWORD=your-secure-password-here

# Slack Webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# PagerDuty
PAGERDUTY_ROUTING_KEY=your-pagerduty-routing-key

# SMTP for Email Alerts
SMTP_USERNAME=alerts@legal-ai-system.com
SMTP_PASSWORD=your-smtp-password
```

## Alert Testing

### 1. Test Prometheus Scraping

```bash
# Check if Prometheus is scraping targets
curl http://localhost:9090/api/v1/targets

# Query metrics
curl 'http://localhost:9090/api/v1/query?query=up'
```

### 2. Test Alert Rules

```bash
# Trigger a test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert"
    }
  }]'
```

### 3. Test Slack Integration

Create a test alert rule:

```yaml
- alert: TestSlackAlert
  expr: vector(1)
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Test Slack notification"
```

### 4. Silence Alerts

```bash
# Create a silence
curl -X POST http://localhost:9093/api/v1/silences \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [{
      "name": "alertname",
      "value": "TestAlert",
      "isRegex": false
    }],
    "startsAt": "2025-10-14T10:00:00Z",
    "endsAt": "2025-10-14T12:00:00Z",
    "createdBy": "admin",
    "comment": "Planned maintenance"
  }'
```

## SLOs (Service Level Objectives)

Define SLOs for the Legal AI System:

| Service | SLO | Target | Measurement |
|---------|-----|--------|-------------|
| **API Availability** | Uptime | 99.9% | `up{job="legal-ai-backend"}` |
| **API Latency** | P95 response time | < 500ms | `http_request_duration_seconds` |
| **Error Rate** | 5xx errors | < 0.1% | `http_requests_total{status=~"5.."}` |
| **Database** | Query latency | < 100ms | `pg_stat_activity_max_tx_duration` |
| **Document Processing** | Success rate | > 99% | `document_processing_success_rate` |

### SLO Dashboard

```promql
# Availability (30 days)
avg_over_time(up{job="legal-ai-backend"}[30d]) * 100

# Error Budget Remaining
(1 - (
  sum(rate(http_requests_total{status=~"5.."}[30d]))
  /
  sum(rate(http_requests_total[30d]))
)) * 100

# P95 Latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Runbooks

Create runbook documentation for each alert:

**`docs/runbooks/service-down.md`**:
```markdown
# Runbook: Service Down

## Alert
ServiceDown - Service is not responding to health checks

## Severity
Critical

## Impact
Users cannot access the service

## Investigation
1. Check if service is running: `docker ps | grep legal-ai-backend`
2. Check service logs: `docker logs legal-ai-backend`
3. Check resource usage: `docker stats legal-ai-backend`
4. Check recent deployments: `git log --oneline -10`

## Resolution
1. Restart service: `docker restart legal-ai-backend`
2. If restart fails, check for:
   - Database connectivity
   - Redis connectivity
   - Disk space
   - Memory limits
3. Roll back recent deployment if needed
4. Scale horizontally if load-related

## Prevention
- Set up auto-restart policies
- Implement circuit breakers
- Add request timeouts
- Monitor resource usage trends
```

## On-Call Rotation

### PagerDuty Schedule

1. **Primary On-Call**: Receives all critical alerts
2. **Secondary On-Call**: Escalation after 15 minutes
3. **Manager On-Call**: Escalation after 30 minutes

### Escalation Policy

```
Critical Alert Fired
    ↓
Primary On-Call (Immediate)
    ↓ (15 min no response)
Secondary On-Call
    ↓ (15 min no response)
Manager On-Call
    ↓ (15 min no response)
All Engineering Team
```

## Maintenance Windows

Schedule maintenance to suppress alerts:

```yaml
# Create maintenance window silence
route:
  routes:
    - match:
        severity: warning
      receiver: 'null'
      active_time_intervals:
        - maintenance_window

time_intervals:
  - name: maintenance_window
    time_intervals:
      - times:
          - start_time: '02:00'
            end_time: '04:00'
        weekdays: ['sunday']
```

## Cost Optimization

### Metrics Retention

- **High-resolution** (15s): 7 days
- **Medium-resolution** (1m): 30 days
- **Low-resolution** (5m): 90 days

### Alert Throttling

- Group related alerts (30s window)
- Throttle repeat notifications (4h)
- Auto-resolve after 5m

## Next Steps

1. ✅ Deploy monitoring stack
2. ✅ Configure alert rules
3. ✅ Set up notification channels
4. ✅ Import Grafana dashboards
5. ✅ Test alert delivery
6. ✅ Create runbooks for critical alerts
7. ✅ Set up on-call rotation
8. ✅ Document SLOs

---

**Questions?** Check Prometheus/Grafana documentation
**Issues?** Review alert rules and targets
**Need Help?** Contact DevOps team
