# PACER Authentication - Quick Reference for Claude Code

## 🎯 TL;DR

**Status**: ✅ Fully implemented in `src/pacer/` and `backend/app/src/services/pacer_service.py`

**Three-step workflow**:
1. **Authenticate**: `POST https://pacer.login.uscourts.gov/services/cso-auth` → get `nextGenCSO` token
2. **Persist**: Store encrypted token in Redis (12-min TTL)
3. **Use**: Include token as `Cookie: nextGenCSO={token}` in all requests

---

## ⚠️ CRITICAL: loginResult Values

**`loginResult: "0"` = SUCCESS** ✅
**Any non-zero value = FAILURE** ❌

```python
# CORRECT ✅
if login_result == "0":
    token = data["nextGenCSO"]
    # Success!

# WRONG ❌
if login_result == "success":
    # This will never work - PACER returns "0" not "success"
```

Even if `errorDescription` is present with `loginResult: "0"`, it's still a **success** (just with a warning).

---

## 📋 Authentication Request

```python
# Request
POST https://pacer.login.uscourts.gov/services/cso-auth
Headers:
  Content-Type: application/json
  Accept: application/json

Body:
{
  "loginId": "username",
  "password": "password",
  "clientCode": "OPTIONAL_BILLING_CODE",  # Required for search if org requires
  "twoFactorCode": "123456",              # If MFA enabled (6-digit TOTP)
  "redactFlag": "1"                       # Required if registered filer
}

# Response (Success)
{
  "nextGenCSO": "128-character-token...",
  "loginResult": "0",  # "0" = SUCCESS
  "errorDescription": ""
}

# Response (Success with Warning)
{
  "nextGenCSO": "128-character-token...",
  "loginResult": "0",  # Still success!
  "errorDescription": "Client code required for search privileges"
}

# Error Responses
{
  "loginResult": "13",  # Invalid credentials (NON-ZERO = FAILURE)
  "errorDescription": "Invalid username, password, or one-time passcode"
}
{
  "loginResult": "5",  # Any non-zero = failure
  "errorDescription": "Account disabled - contact PACER Service Center"
}
```

**Environments**:
- **QA** (testing): `https://qa-login.uscourts.gov`
- **Production**: `https://pacer.login.uscourts.gov`

---

## 💾 Token Persistence

**Implementation**: `src/pacer/auth/authenticator.py:573-630`

```python
# 1. Hash username for privacy (SHA-256)
username_hash = hashlib.sha256(username.encode()).hexdigest()

# 2. Encrypt token (Fernet/AES-128)
encrypted_token = fernet.encrypt(token.encode())

# 3. Store in Redis with TTL
redis_key = f"pacer:token:{username_hash}"
await redis_client.setex(redis_key, 720, encrypted_token)  # 12 minutes

# 4. Retrieve and decrypt
encrypted = await redis_client.get(redis_key)
token = fernet.decrypt(encrypted).decode()
```

**Why 12 minutes?** PACER sessions expire after 15 minutes. Cache for 12 to provide buffer.

---

## 🔐 Using Token in Requests

### Method 1: Cookie (Preferred)

```python
headers = {
    "Cookie": f"nextGenCSO={token}",
    "User-Agent": "PACER-Legal-AI-System/1.0"
}

# If clientCode was used during auth
headers["Cookie"] += f"; PacerClientCode={client_code}"

# Make request
response = await client.get(pacer_url, headers=headers)

# Handle 401 = token expired
if response.status_code == 401:
    # Re-authenticate and retry
    token = await authenticator.authenticate(username, password)
```

### Method 2: Header (PCL API)

```python
headers = {
    "X-PACER-Token": token,
    "Content-Type": "application/json"
}
```

---

## 📦 Using Existing Implementation

### Option A: Core Authenticator (Single User)

```python
from src.pacer.auth.authenticator import PACERAuthenticator

# Initialize
authenticator = PACERAuthenticator(environment="production")

# Authenticate (uses cache automatically)
result = await authenticator.authenticate(
    username="your_username",
    password="your_password",
    client_code="YOUR_CLIENT_CODE",  # Optional
    otp="123456"  # If MFA enabled
)

token = result["nextGenCSO"]
print(f"Cached: {result['cached']}")  # True if from cache

# Use token in requests
headers = {"Cookie": f"nextGenCSO={token}"}
response = await client.get(url, headers=headers)

# Cleanup
await authenticator.close()
```

### Option B: Service Layer (Multi-User)

```python
from backend.app.src.services.pacer_service import PACERService

# Initialize with database session
service = PACERService(db)

# Save user credentials (one-time setup)
await service.save_user_credentials(
    user_id=123,
    pacer_username="user_pacer_account",
    pacer_password="user_pacer_password",
    client_code="CLIENT_CODE",
    daily_limit=100.0
)

# Authenticate user (automatic caching)
token = await service.authenticate_user(user_id=123)

# Search cases (handles auth automatically)
results = await service.search_cases(
    user_id=123,
    court="nysd",
    case_number="1:24-cv-00123"
)
```

### Option C: REST API (Frontend)

```bash
# Save credentials
curl -X POST http://localhost:8000/api/v1/pacer/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "pacer_username": "username",
    "pacer_password": "password",
    "client_code": "CODE",
    "daily_limit": 100.0
  }'

# Authenticate
curl -X POST http://localhost:8000/api/v1/pacer/authenticate

# Search cases
curl -X POST http://localhost:8000/api/v1/pacer/search/cases \
  -H "Content-Type: application/json" \
  -d '{
    "court": "nysd",
    "case_number": "1:24-cv-00123"
  }'
```

---

## 🚨 Error Handling

```python
from src.pacer.auth.authenticator import (
    PACERAuthenticator,
    PACERMFARequiredError,
    PACERInvalidCredentialsError,
    PACERRateLimitError,
    PACERAuthenticationError
)

try:
    result = await authenticator.authenticate(username, password)
    token = result["nextGenCSO"]

except PACERMFARequiredError:
    # Get OTP and retry
    otp = input("Enter OTP: ")
    result = await authenticator.authenticate(username, password, otp=otp)

except PACERInvalidCredentialsError:
    # Wrong username/password
    print("Invalid credentials")

except PACERRateLimitError as e:
    # Too many attempts (5 in 5 minutes)
    print(f"Rate limited: {e}")
    # Wait or clear rate limit (admin)

except PACERAuthenticationError as e:
    # General auth error
    print(f"Auth failed: {e}")
```

---

## 💰 Cost Tracking

```python
from src.pacer.downloads.cost_tracker import CostTracker, PACEROperation

# Initialize tracker
tracker = CostTracker(daily_limit=50.0, monthly_limit=500.0)

# Check affordability before operation
can_afford, cost, reason = await tracker.can_afford_operation(
    PACEROperation.DOCUMENT_DOWNLOAD,
    pages=10
)

if not can_afford:
    print(f"Cannot download: {reason}")
    return

print(f"Estimated cost: ${cost:.2f}")  # $1.00 (10 pages × $0.10)

# Record actual cost after operation
await tracker.record_cost(
    operation=PACEROperation.DOCUMENT_DOWNLOAD,
    user_id="user123",
    pages=10,
    cost=1.00,
    court="nysd"
)

# Get usage report
report = tracker.get_usage_report(user_id="user123")
print(f"Daily spending: ${report['daily_spending']:.2f}")
```

**PACER Pricing**:
- Searches: **FREE**
- Documents: **$0.10/page** (max $3.00 per doc)
- Quarterly free: **$30.00**

---

## 🔧 Configuration

**Environment Variables** (`.env`):

```bash
# Required
PACER_USERNAME=your_username
PACER_PASSWORD=your_password

# Optional
PACER_CLIENT_CODE=billing_code
PACER_ENVIRONMENT=production  # or "qa"
PACER_MAX_DAILY_COST=100.00
PACER_TOKEN_CACHE_TTL=720  # seconds (12 minutes)

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

---

## 🧪 Testing

```bash
# Start Redis
redis-server

# Test authentication
python -m src.pacer.auth.authenticator

# Test full workflow
python -m src.pacer.example_integration

# Start backend API
cd backend
uvicorn main:app --reload

# Test API endpoint
curl http://localhost:8000/api/v1/pacer/credentials/status
```

---

## 📍 Key Files

| Component | File Path |
|-----------|-----------|
| Core Authenticator | `src/pacer/auth/authenticator.py` |
| Token Manager | `src/pacer/auth/token_manager.py` |
| MFA Handler | `src/pacer/auth/mfa_handler.py` |
| PCL API Client | `src/pacer/api/pcl_client.py` |
| Document Fetcher | `src/pacer/downloads/document_fetcher.py` |
| Cost Tracker | `src/pacer/downloads/cost_tracker.py` |
| Service Layer | `backend/app/src/services/pacer_service.py` |
| API Endpoints | `backend/app/api/pacer_endpoints.py` |
| Models | `src/pacer/models/pacer_models.py` |

---

## 🆘 Common Issues

### "Invalid credentials"
- ✅ Check username/password
- ✅ Add OTP if MFA enabled
- ✅ Add `redactFlag="1"` if filer account
- ✅ Add `clientCode` if required for search

### "Token expired"
```python
# Force refresh
result = await authenticator.authenticate(
    username, password, force_refresh=True
)
```

### "Rate limit exceeded"
```python
# Check status
status = await service.get_rate_limit_status(user_id)
print(f"Wait {status['reset_in_seconds']} seconds")

# Clear (admin only)
await service.clear_rate_limit(user_id)
```

### "Redis connection failed"
```bash
# Start Redis
redis-server

# Test connection
redis-cli ping  # Should return PONG
```

---

## 🎓 MFA/TOTP Setup

```python
from src.pacer.auth.mfa_handler import MFAHandler

# Get TOTP secret from PACER account settings
totp_secret = "BASE32_SECRET_FROM_PACER"

# Initialize handler
mfa = MFAHandler(totp_secret=totp_secret)

# Generate OTP automatically
otp = mfa.generate_otp()  # 6-digit code

# Use in authentication
result = await authenticator.authenticate(
    username, password, otp=otp
)
```

---

## 📚 Complete Examples

**Example 1: Search Cases**
```python
from src.pacer.auth.authenticator import PACERAuthenticator
from src.pacer.api.pcl_client import PCLClient

# Authenticate
auth = PACERAuthenticator(environment="production")
result = await auth.authenticate("username", "password")
token = result["nextGenCSO"]

# Search
client = PCLClient(auth_token=token)
results = await client.search_cases(
    court="nysd",
    case_number="1:24-cv-00123",
    filed_from="2024-01-01"
)

print(f"Found {results.total_count} cases")
for case in results.results:
    print(f"  {case['caseNumber']}: {case['caseTitle']}")
```

**Example 2: Download Document**
```python
from src.pacer.auth.authenticator import PACERAuthenticator
from src.pacer.downloads.document_fetcher import DocumentFetcher
from src.pacer.downloads.cost_tracker import CostTracker

# Authenticate
auth = PACERAuthenticator()
result = await auth.authenticate("username", "password")

# Setup cost tracking
tracker = CostTracker(daily_limit=50.0)

# Download
fetcher = DocumentFetcher(auth_token=result["nextGenCSO"], cost_tracker=tracker)
result = await fetcher.fetch_document(
    document_url="https://ecf.nysd.uscourts.gov/doc1/123456",
    case_id="1:24-cv-00123",
    document_id="doc-1",
    user_id="user123",
    estimated_pages=10
)

print(f"Downloaded: {result['file_path']}")
print(f"Cost: ${result['cost']:.2f}")
```

---

## ✅ Implementation Checklist

- [x] ✅ Authentication with nextGenCSO token
- [x] ✅ Encrypted token persistence in Redis
- [x] ✅ Token validation before use
- [x] ✅ Automatic token refresh
- [x] ✅ MFA/OTP support
- [x] ✅ Rate limiting (5 attempts/5 min)
- [x] ✅ Cost tracking with limits
- [x] ✅ Multi-user support
- [x] ✅ Error handling and retry logic
- [x] ✅ REST API endpoints
- [x] ✅ Comprehensive logging
- [x] ✅ Security (encryption, sanitization)

**Status**: Production-ready ✅

---

**Quick Start**: `python -m src.pacer.example_integration`

**Full Docs**: `docs/PACER_AUTHENTICATION_IMPLEMENTATION_GUIDE.md`

**Support**: Check logs in `logs/pacer_integration.log`
