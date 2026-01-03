# Sentry Error Tracking Setup Guide

**Status:** ✅ Configured
**Priority:** High (Production)
**Last Updated:** 2025-10-14

## Overview

Sentry provides real-time error tracking and performance monitoring for production environments. This guide covers setup, configuration, and best practices for the Legal AI System.

## Why Sentry?

- **Real-time Error Tracking**: Get notified immediately when errors occur in production
- **Performance Monitoring**: Track slow endpoints and database queries
- **Release Tracking**: Monitor errors across different deployments
- **Context-Rich**: See full stack traces, user context, and breadcrumbs
- **Privacy-First**: Automatic PII filtering for legal applications

## Setup Instructions

### 1. Create Sentry Account & Project

1. Sign up at [sentry.io](https://sentry.io)
2. Create a new project (select "FastAPI" as platform)
3. Copy your DSN (Data Source Name)

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Enable Sentry error tracking
SENTRY_ENABLED=true

# Your Sentry DSN
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0

# Environment name (helps organize errors by deployment)
ENVIRONMENT=production
```

**Important:**
- Set `SENTRY_ENABLED=true` in production only
- Keep `SENTRY_ENABLED=false` in development to avoid noise
- Use different Sentry projects for staging and production

### 3. Install Dependencies

Sentry SDK is already included in `requirements.txt`:

```bash
sentry-sdk[fastapi]==1.38.0
```

If not installed, run:
```bash
pip install sentry-sdk[fastapi]
```

### 4. Verify Installation

Start your backend and look for:

```
=============================================================
ERROR TRACKING CONFIGURATION
=============================================================
SUCCESS: Sentry error tracking configured
=============================================================
```

### 5. Test Error Tracking

Create a test error to verify Sentry is working:

```python
# In your browser, visit:
http://localhost:8000/test-sentry

# Or use curl:
curl http://localhost:8000/test-sentry
```

You should see the error appear in your Sentry dashboard within seconds.

## Configuration Details

### Current Settings

The Legal AI System uses these Sentry configurations:

```python
sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,

    # Integrations
    integrations=[
        FastApiIntegration(auto_enabling_integrations=True),  # FastAPI support
        SqlalchemyIntegration(),  # Database query tracking
    ],

    # Performance Monitoring
    traces_sample_rate=0.1,  # Track 10% of requests
    profiles_sample_rate=0.1,  # Profile 10% of traces

    # Security & Privacy
    attach_stacktrace=True,  # Full stack traces
    send_default_pii=False,  # Never send PII automatically

    # Data Filtering
    before_send=filter_sentry_event,  # Custom filter for sensitive data

    # Release Tracking
    release="legal-ai-system@1.0.0",  # Track by version
)
```

### Privacy & Data Filtering

**Critical for legal applications**: Sentry automatically filters sensitive data before transmission.

#### Filtered Data

The system filters:
- **Headers**: Authorization, Cookie, X-API-Key, X-Auth-Token
- **Form Data**: password, token, secret, key, api_key
- **Legal Data**: SSN, social_security, credit_card, CVV
- **Exception Messages**: API keys (sk-, api_, token_)

#### Filter Function

Located in `backend/main.py`:

```python
def filter_sentry_event(event, hint):
    """Filter sensitive data from Sentry events"""
    # Remove sensitive headers
    if 'request' in event and 'headers' in event['request']:
        sensitive_headers = ['authorization', 'cookie', 'x-api-key']
        for header in sensitive_headers:
            event['request']['headers'].pop(header.lower(), None)

    # Remove sensitive form data
    if 'request' in event and 'data' in event['request']:
        sensitive_fields = ['password', 'token', 'secret', 'key']
        # ... filter logic

    return event
```

## Features

### 1. Error Tracking

All unhandled exceptions are automatically sent to Sentry with:
- Full stack trace
- Request context (URL, method, headers)
- User context (if authenticated)
- Server environment info
- Breadcrumbs (events leading to error)

### 2. Performance Monitoring

Tracks:
- **Request Duration**: Slow API endpoints
- **Database Queries**: Slow database operations
- **External API Calls**: Slow AI service requests
- **Throughput**: Requests per second

### 3. Release Tracking

Errors are grouped by release version:
- Track regression bugs
- Compare error rates between deployments
- Roll back problematic releases

### 4. Alerts

Configure alerts in Sentry for:
- New error types
- Error frequency spikes
- Performance degradation
- Specific error patterns

## Best Practices

### 1. Environment Separation

Use separate Sentry projects for each environment:

```bash
# Development - Disabled
SENTRY_ENABLED=false

# Staging
SENTRY_ENABLED=true
ENVIRONMENT=staging
SENTRY_DSN=<staging-dsn>

# Production
SENTRY_ENABLED=true
ENVIRONMENT=production
SENTRY_DSN=<production-dsn>
```

### 2. Custom Context

Add custom context to errors:

```python
from sentry_sdk import capture_exception, set_user, set_context

# Set user context
set_user({"id": user.id, "email": user.email})

# Set custom context
set_context("legal_case", {
    "case_id": case.id,
    "case_number": case.number,
    "jurisdiction": case.jurisdiction
})

# Capture exception with context
try:
    process_legal_document(document)
except Exception as e:
    capture_exception(e)
```

### 3. Breadcrumbs

Add breadcrumbs for debugging:

```python
from sentry_sdk import add_breadcrumb

add_breadcrumb(
    category='document_processing',
    message='Started OCR processing',
    level='info',
    data={'document_id': doc.id, 'pages': doc.page_count}
)
```

### 4. Performance Transactions

Track custom operations:

```python
import sentry_sdk

with sentry_sdk.start_transaction(op="ai_analysis", name="legal_document_analysis"):
    # Your code here
    result = analyze_document(document)
```

## Dashboard Setup

### Recommended Alerts

1. **High Error Rate**: > 10 errors/minute
2. **New Error Types**: Any new unique error
3. **Performance Regression**: P95 latency > 2 seconds
4. **Database Errors**: Any database connection issues
5. **External Service Failures**: AI API errors

### Dashboard Widgets

Create dashboards for:
- Error frequency by endpoint
- Response time percentiles (P50, P95, P99)
- Database query performance
- AI service uptime
- User-facing errors vs. system errors

## Troubleshooting

### Sentry Not Receiving Events

**Check:**
1. `SENTRY_ENABLED=true` in `.env`
2. Valid `SENTRY_DSN` configured
3. Internet connectivity from server
4. Sentry SDK installed: `pip list | grep sentry`
5. Check startup logs for Sentry initialization

### Too Many Events

**Solutions:**
1. Increase sample rates to reduce volume:
   ```python
   traces_sample_rate=0.05  # Only 5% of requests
   ```
2. Filter specific errors:
   ```python
   def before_send(event, hint):
       # Ignore specific errors
       if 'ConnectionError' in event.get('exception', {}).get('values', [{}])[0].get('type', ''):
           return None  # Don't send to Sentry
       return event
   ```

### PII Leakage Concerns

**Verification:**
1. Check `send_default_pii=False` is set
2. Review `filter_sentry_event` function
3. Test with sample data
4. Review Sentry events manually
5. Enable Sentry's PII data scrubbing rules

### Development Noise

Disable Sentry in development:

```bash
# .env.development
SENTRY_ENABLED=false
```

## Integration with CI/CD

### Release Tracking

Automatically track releases:

```bash
# In your deployment script
export SENTRY_RELEASE=$(git rev-parse HEAD)

# Upload source maps (for frontend)
sentry-cli releases new $SENTRY_RELEASE
sentry-cli releases set-commits $SENTRY_RELEASE --auto
sentry-cli releases finalize $SENTRY_RELEASE
```

### Deployment Notifications

Notify Sentry of deployments:

```bash
sentry-cli releases deploys $SENTRY_RELEASE new -e production
```

## Cost Optimization

Sentry pricing is based on events sent. Optimize costs:

1. **Sample Rates**: Adjust based on traffic
   - Low traffic (< 1000 req/day): 100% sampling
   - Medium traffic (< 10k req/day): 50% sampling
   - High traffic (> 10k req/day): 10-20% sampling

2. **Filter Noise**: Ignore known errors
3. **Rate Limiting**: Use Sentry's rate limiting features
4. **Spike Protection**: Enable spike protection in Sentry settings

## Security Considerations

### Data Residency

- Sentry stores data in US by default
- EU region available (may cost extra)
- Self-hosted option for sensitive data

### Compliance

- **GDPR**: Sentry is GDPR compliant
- **SOC 2**: Sentry is SOC 2 Type II certified
- **HIPAA**: BAA available for healthcare data

### Access Control

- Use role-based access in Sentry
- Limit who can view error data
- Enable 2FA for all Sentry users
- Audit access logs regularly

## Support & Resources

- **Sentry Documentation**: https://docs.sentry.io/platforms/python/guides/fastapi/
- **FastAPI Integration**: https://docs.sentry.io/platforms/python/guides/fastapi/
- **Python SDK**: https://docs.sentry.io/platforms/python/
- **Status Page**: https://status.sentry.io/

## Next Steps

After Sentry is configured:

1. ✅ Set up error alerts
2. ✅ Create custom dashboards
3. ✅ Configure release tracking
4. ✅ Test error notifications
5. ✅ Train team on error triage
6. ✅ Integrate with Slack/PagerDuty
7. ✅ Set up performance monitoring
8. ✅ Configure issue ownership rules

---

**Configured By:** Production Readiness Implementation
**Questions?** Check backend logs or Sentry documentation
