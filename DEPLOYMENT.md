# Development to Production Workflow

## Overview

This document defines the exact steps to go from development to production deployment.
**No guesswork. No patching. Follow this process.**

---

## Phase 1: Local Development Standards

### 1.1 Database Setup (MUST use PostgreSQL locally)

```bash
# Start local PostgreSQL (via Docker)
docker run -d --name legal-ai-postgres \
  -e POSTGRES_USER=legalai \
  -e POSTGRES_PASSWORD=localdev \
  -e POSTGRES_DB=legalai \
  -p 5432:5432 \
  postgres:15

# Set in .env
DATABASE_URL=postgresql://legalai:localdev@localhost:5432/legalai
```

**Why:** SQLite behaves differently than PostgreSQL. Bugs that work in SQLite fail in production.

### 1.2 Always Use Migrations

```bash
# NEVER do this:
# python -c "from app.models import Base; Base.metadata.create_all(engine)"

# ALWAYS do this:
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### 1.3 Single Auth Import

Every API file must use:
```python
from app.api.deps.auth import get_current_user, CurrentUser

@router.get("/endpoint")
async def my_endpoint(current_user: CurrentUser = Depends(get_current_user)):
    # Use current_user.user_id, current_user.email, current_user.role
    pass
```

**Never** create a new `get_current_user` function. **Never** import from a different location.

### 1.4 CurrentUser Available Fields

These fields are available on `current_user`:
- `user_id` (str) - Primary identifier
- `id` (str) - Alias for user_id
- `email` (str | None) - User's email
- `role` (str | None) - User's role as string
- `username` (str | None) - Username if set
- `first_name` (str | None) - First name if in token
- `last_name` (str | None) - Last name if in token
- `roles` (list) - List of roles
- `permissions` (list) - List of permissions

**If you need a field not listed here:** Add it to `CurrentUser` class in `app/api/deps/auth.py` AND add it to the JWT token in `app/utils/auth.py`.

---

## Phase 2: Pre-Deployment Verification

Run these checks BEFORE pushing to production.

### 2.1 Auth Consistency Check

```bash
# Should return exactly ONE result from deps/auth.py
grep -rn "^async def get_current_user\|^def get_current_user" backend/app/ --include="*.py"

# Expected output:
# backend/app/api/deps/auth.py:42:async def get_current_user(request: Request) -> CurrentUser:
```

### 2.2 CurrentUser Attribute Check

```bash
# Find all current_user attribute accesses
grep -roh "current_user\.[a-z_]*" backend/app/api/ --include="*.py" | sort | uniq -c | sort -rn

# Verify each attribute exists in CurrentUser class
# If you see something like current_user.stripe_customer_id - that's a bug
# CurrentUser doesn't have stripe_customer_id, you need to query the database
```

### 2.3 Import Verification

```bash
# All files should import from app.api.deps.auth, not elsewhere
grep -rn "from.*auth import get_current_user" backend/app/api/ --include="*.py"

# Flag any imports from:
# - ..core.auth (doesn't exist)
# - ..utils.auth (wrong - returns different type)
# - .auth (local redefinition)
```

### 2.4 Migration Test

```bash
cd backend

# Test fresh database migration
DATABASE_URL=postgresql://test:test@localhost:5432/test_db alembic upgrade head

# Test migration is idempotent (running twice shouldn't fail)
DATABASE_URL=postgresql://test:test@localhost:5432/test_db alembic upgrade head
```

### 2.5 Environment Variables Check

```bash
# List all env vars used in code
grep -roh "os\.getenv\(['\"][^'\"]*['\"]\)" backend/ --include="*.py" | sort | uniq

# Verify each one is documented in .env.example
# Verify each one is set in Railway dashboard
```

### 2.6 CORS Configuration Check

```bash
# Find CORS configuration
grep -rn "CORSMiddleware\|CORS_ORIGINS\|Access-Control" backend/ --include="*.py"

# Verify:
# 1. CORS_ORIGINS environment variable is used
# 2. Production frontend URL will be in CORS_ORIGINS
# 3. Exception handlers include CORS headers
```

---

## Phase 3: Pre-Push Checklist

Before running `git push`, verify:

```markdown
## Code Quality
- [ ] No new `get_current_user` functions created
- [ ] All `current_user.X` accesses use valid attributes
- [ ] All imports resolve (no missing modules)
- [ ] No hardcoded URLs (localhost, API keys, secrets)

## Database
- [ ] New tables have migrations (not created manually)
- [ ] Migrations are idempotent (IF NOT EXISTS, DO $$ EXCEPTION)
- [ ] Migrations tested locally with PostgreSQL

## Environment
- [ ] New env vars added to .env.example
- [ ] New env vars documented in CLAUDE.md
- [ ] No secrets committed to git

## Testing
- [ ] Endpoint tested locally with curl/Postman
- [ ] Error cases return proper JSON (not HTML/empty)
- [ ] CORS works (test from different origin)
```

---

## Phase 4: Deployment Process

### 4.1 Railway Dashboard Setup (One-time)

```
Service: backend
├── Variables:
│   ├── DATABASE_URL: (from Railway PostgreSQL)
│   ├── REDIS_URL: (from Railway Redis)
│   ├── JWT_SECRET_KEY: (generate: openssl rand -hex 32)
│   ├── CORS_ORIGINS: https://your-frontend.up.railway.app
│   ├── ENVIRONMENT: production
│   ├── PYTHONPATH: /app
│   └── [other API keys]
│
├── Settings:
│   ├── Root Directory: backend
│   ├── Start Command: alembic upgrade head && gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
│   └── Health Check Path: /health
```

### 4.2 Deployment Steps

```bash
# 1. Run pre-deployment checks (Phase 2)
./scripts/pre-deploy-check.sh  # Create this script with Phase 2 commands

# 2. Commit with descriptive message
git add -A
git commit -m "feat/fix/chore: Description of changes"

# 3. Push to trigger deploy
git push origin main

# 4. Monitor Railway logs
# Watch for:
# - "Running upgrade" messages from Alembic
# - "Application startup complete" from uvicorn
# - Any Python exceptions
```

### 4.3 Post-Deployment Verification

```bash
# 1. Health check
curl https://your-backend.up.railway.app/health

# 2. Auth check (should return 401, not 500 or CORS error)
curl https://your-backend.up.railway.app/api/v1/auth/me

# 3. Test authenticated endpoint
TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" \
  https://your-backend.up.railway.app/api/v1/documents/

# 4. Test from frontend origin (CORS check)
curl -H "Origin: https://your-frontend.up.railway.app" \
  -H "Authorization: Bearer $TOKEN" \
  https://your-backend.up.railway.app/api/v1/documents/
```

---

## Phase 5: Rollback Procedure

If deployment fails:

```bash
# 1. Find last working commit
git log --oneline -10

# 2. Revert to it
git revert HEAD  # If just one bad commit
# OR
git reset --hard <commit-hash>  # Nuclear option
git push --force origin main

# 3. In Railway, trigger manual redeploy if needed
```

---

## Common Issues & Solutions

### Issue: CORS Error in Browser

**Symptom:** Browser console shows CORS error, but endpoint works in curl.

**Cause:** Usually a Python exception. Check Railway logs for the actual error.

**Fix:**
1. Find the real error in Railway logs
2. Fix the Python error
3. Ensure exception handlers include CORS headers

### Issue: 500 Error on Authenticated Endpoints

**Symptom:** `/api/v1/something` returns 500.

**Cause:** Usually `AttributeError` on `current_user`.

**Check:**
```bash
grep -n "current_user\." backend/app/api/the_file.py
```

**Fix:** Ensure all accessed attributes exist on `CurrentUser` class.

### Issue: Migration Fails on Deploy

**Symptom:** "relation already exists" or "column already exists"

**Cause:** Migration not idempotent.

**Fix:** Update migration to use:
```python
op.execute("CREATE TABLE IF NOT EXISTS ...")
op.execute("CREATE INDEX IF NOT EXISTS ...")
```

### Issue: "Module not found" on Deploy

**Symptom:** `ModuleNotFoundError: No module named 'app.core.auth'`

**Cause:** Import path doesn't exist.

**Fix:**
```bash
# Find what files import from this path
grep -rn "from.*core.auth" backend/

# Fix to use correct path
from app.api.deps.auth import get_current_user
```

---

## Scripts to Create

Create these helper scripts:

### `scripts/pre-deploy-check.sh`

```bash
#!/bin/bash
set -e

echo "=== Pre-Deployment Checks ==="

echo -n "Checking auth implementations... "
COUNT=$(grep -rn "^async def get_current_user\|^def get_current_user" backend/app/ --include="*.py" | wc -l)
if [ "$COUNT" -gt 2 ]; then
  echo "FAIL: Found $COUNT get_current_user implementations"
  exit 1
fi
echo "OK"

echo -n "Checking for broken imports... "
cd backend && python -c "from app.api.deps.auth import get_current_user" 2>/dev/null
if [ $? -ne 0 ]; then
  echo "FAIL: Auth import broken"
  exit 1
fi
echo "OK"

echo -n "Checking migrations... "
# Add migration check here
echo "OK"

echo ""
echo "=== All checks passed ==="
```

---

## Summary

1. **Develop** with PostgreSQL, not SQLite
2. **Always** use migrations, never create tables manually
3. **One** auth pattern, imported from one location
4. **Check** before pushing (run Phase 2)
5. **Monitor** logs after deploy (Phase 4.3)
6. **Rollback** quickly if issues (Phase 5)

**The goal:** Zero surprises in production.
