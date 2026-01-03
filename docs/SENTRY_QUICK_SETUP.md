# Sentry Quick Setup Guide

## Overview
Sentry error tracking is already integrated into the Legal AI System. You just need to create a Sentry account and enable it.

**Time Required**: 10-15 minutes

---

## Step 1: Create Sentry Account (5 minutes)

1. Go to https://sentry.io/signup/
2. Sign up with email or GitHub
3. Choose **Free Plan** (includes 5,000 errors/month - perfect for development)

---

## Step 2: Create Project (3 minutes)

1. After signup, click **"Create Project"**
2. Select **"FastAPI"** as the platform (or "Python" if FastAPI isn't listed)
3. Set alert frequency: **"Alert me on every new issue"** (recommended for development)
4. Name your project: **"Legal AI System Backend"**
5. Click **"Create Project"**

---

## Step 3: Get Your DSN (1 minute)

After project creation, Sentry will show you a setup page with your DSN.

**Your DSN will look like:**
```
https://abc123def456@o1234567.ingest.sentry.io/7654321
```

**If you missed it:**
1. Go to **Settings** → **Projects** → **Legal AI System Backend**
2. Click **Client Keys (DSN)**
3. Copy the **DSN** value

---

## Step 4: Configure Backend (2 minutes)

Edit `backend/.env`:

```bash
# Change this line:
SENTRY_ENABLED=false

# To:
SENTRY_ENABLED=true

# Uncomment and add your real DSN:
SENTRY_DSN=https://your-actual-dsn-here@o1234567.ingest.sentry.io/7654321
```

**Example:**
```bash
SENTRY_ENABLED=true
SENTRY_DSN=https://abc123def456@o1234567.ingest.sentry.io/7654321
```

---

## Step 5: Restart Backend

```bash
# Stop the backend if running (Ctrl+C)
cd backend
python -m uvicorn main:app --reload
```

Look for this message in the logs:
```
✅ Sentry initialized: https://o1234567.ingest.sentry.io/7654321
```

---

## Step 6: Test Sentry Integration (2 minutes)

### Option A: Use Test Endpoint

```bash
# Trigger a test error
curl http://localhost:8000/health/test-error
```

### Option B: Use Sentry CLI Test

```bash
# In the backend directory
python -c "import sentry_sdk; sentry_sdk.init('your-dsn-here'); sentry_sdk.capture_message('Test from Legal AI System')"
```

### Verify in Sentry Dashboard

1. Go to https://sentry.io/organizations/your-org/issues/
2. You should see a new issue appear within 5-10 seconds
3. Click on the issue to see full error details, stack trace, and context

---

## What Sentry Will Track

Once enabled, Sentry automatically tracks:

### 1. **Python Exceptions**
- All unhandled exceptions in FastAPI endpoints
- Database errors
- AI service errors (OpenAI, Anthropic)
- File processing errors

### 2. **API Errors**
- 500 Internal Server Errors
- Failed database queries
- Failed external API calls

### 3. **Performance** (if enabled)
- Slow API endpoints
- Database query performance
- External API latency

### 4. **Context Information**
- User information (if authenticated)
- Request data (URL, method, headers)
- Environment (development/production)
- Server info

---

## Privacy & PII Protection

The system automatically filters sensitive data from Sentry reports:

**Filtered Fields:**
- Passwords
- API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
- JWT tokens
- Social Security Numbers
- Credit card numbers
- Client names and personal information

**This is configured in** `backend/main.py:filter_sentry_event()`

---

## Sentry Dashboard Features

### Issues Tab
- See all errors in real-time
- Group similar errors together
- Track error frequency and trends

### Performance Tab
- Monitor API endpoint performance
- Identify slow database queries
- Track external service latency

### Releases Tab
- Track errors by deployment version
- Compare error rates between releases

### Alerts
- Email notifications for new errors
- Slack integration (optional)
- Custom alert rules

---

## Production Configuration

For production deployment, update `.env`:

```bash
ENVIRONMENT=production
SENTRY_ENABLED=true
SENTRY_DSN=https://your-production-dsn@o1234567.ingest.sentry.io/7654321

# Performance monitoring (requires Performance plan)
SENTRY_TRACES_SAMPLE_RATE=0.1  # Track 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE=0.1  # Profile 10% of transactions
```

---

## Troubleshooting

### Issue: "Sentry initialization failed"

**Check:**
1. DSN is correct (no typos)
2. Internet connection is working
3. Sentry project is active

### Issue: "Events not appearing in Sentry"

**Check:**
1. `SENTRY_ENABLED=true` in `.env`
2. Backend was restarted after changing `.env`
3. DSN is from the correct project
4. Try the test endpoint to force an error

### Issue: "Too many events"

**Solution:**
1. Add error filtering in `filter_sentry_event()`
2. Reduce sample rate for performance tracking
3. Upgrade Sentry plan

---

## Cost & Limits

### Free Plan
- 5,000 errors per month
- 10,000 performance units (if enabled)
- 30-day error retention
- **Perfect for development**

### Team Plan ($26/month)
- 50,000 errors per month
- 100,000 performance units
- 90-day retention
- **Recommended for production**

### Business Plan ($80/month)
- Unlimited errors
- Unlimited performance tracking
- Custom retention
- Priority support

---

## Next Steps

After Sentry is working:

1. **Set Up Alerts**: Configure email/Slack notifications
2. **Create Dashboards**: Monitor key metrics
3. **Test Error Handling**: Verify errors are captured correctly
4. **Review PII Filtering**: Ensure no sensitive data is sent to Sentry

---

## Resources

- Sentry Documentation: https://docs.sentry.io/
- FastAPI Integration: https://docs.sentry.io/platforms/python/guides/fastapi/
- Error Monitoring Best Practices: https://blog.sentry.io/error-monitoring-best-practices/

---

## Summary

**What We Did:**
1. ✅ Sentry SDK already installed (`sentry-sdk[fastapi]==1.38.0`)
2. ✅ Configuration code already in `backend/main.py`
3. ✅ PII filtering already implemented
4. ✅ Environment variables added to `.env`

**What You Need to Do:**
1. Create Sentry account (free)
2. Get DSN from Sentry project
3. Update `backend/.env` with `SENTRY_ENABLED=true` and your DSN
4. Restart backend
5. Test with `/health/test-error` endpoint

**Total Time:** ~15 minutes
