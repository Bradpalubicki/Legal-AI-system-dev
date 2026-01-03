# PACER Integration Setup

## Overview
This directory contains the PACER (Public Access to Court Electronic Records) integration for the Legal AI System.

## Components

### Authentication (`src/pacer/auth/`)
- `authenticator.py` - PACER authentication with token caching
- `token_manager.py` - Token lifecycle management
- `mfa_handler.py` - Multi-factor authentication support

### API Client (`src/pacer/api/`)
- `pcl_client.py` - PACER Case Locator API client
- `case_search.py` - Case search implementation
- `party_search.py` - Party search implementation
- `batch_handler.py` - Batch search operations

### Downloads (`src/pacer/downloads/`)
- `document_fetcher.py` - Document download with retry logic
- `cost_tracker.py` - PACER cost monitoring and alerts
- `storage_handler.py` - Secure document storage

### Models (`src/pacer/models/`)
- `pacer_models.py` - Pydantic models for PACER data

## Setup Instructions

1. **Run Setup Script**
   ```bash
   python setup_pacer_auth.py
   ```

2. **Configure Credentials**
   Edit `.env` and add your PACER credentials:
   ```
   PACER_USERNAME=your_username
   PACER_PASSWORD=your_password
   PACER_CLIENT_CODE=your_client_code
   ```

3. **Start Redis**
   ```bash
   # Windows (with Chocolatey)
   choco install redis-64
   redis-server

   # Linux/Mac
   redis-server
   ```

4. **Test Authentication**
   ```bash
   python -m src.pacer.auth.authenticator
   ```

## Security Notes

- Encryption keys are stored in `keys/` directory (NOT committed to git)
- Tokens are cached in Redis with 3-hour expiration
- All credentials are encrypted at rest
- Cost limits are enforced to prevent billing overruns

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PACER_USERNAME` | PACER login username | Required |
| `PACER_PASSWORD` | PACER login password | Required |
| `PACER_CLIENT_CODE` | PACER client code for billing | Optional |
| `PACER_ENVIRONMENT` | Environment (production/qa) | production |
| `PACER_MAX_DAILY_COST` | Maximum daily spending limit | $100.00 |
| `PACER_TOKEN_CACHE_TTL` | Token cache duration (seconds) | 10800 |

## Cost Management

PACER charges per page accessed. The integration includes:
- Real-time cost tracking
- Daily spending limits
- Cost alerts at 75% threshold
- Detailed usage reports

## Usage Example

```python
from src.pacer.auth.authenticator import PACERAuthenticator
from src.pacer.api.pcl_client import PCLClient

# Authenticate
auth = PACERAuthenticator(environment="production")
result = await auth.authenticate(
    username="your_username",
    password="your_password"
)

# Search cases
client = PCLClient(auth_token=result["nextGenCSO"])
cases = await client.search_cases(
    case_number="1:24-cv-00123",
    court="nysd"
)
```

## Troubleshooting

### Redis Connection Issues
- Ensure Redis is running: `redis-cli ping`
- Check port 6379 is not blocked
- Verify REDIS_HOST and REDIS_PORT in .env

### Authentication Failures
- Verify PACER credentials are correct
- Check if account has active billing
- Ensure environment (production/qa) matches your account

### Token Expiration
- Tokens are auto-refreshed when expired
- Manual refresh: `auth.refresh_token()`
- Check Redis for cached tokens: `redis-cli KEYS "pacer:token:*"`

## Support

For issues:
1. Check logs in `logs/pacer_integration.log`
2. Review Redis cache: `redis-cli MONITOR`
3. Verify credentials in PACER web interface
4. Contact PACER support: https://pacer.uscourts.gov/help

## Compliance

⚠ **IMPORTANT**: All PACER access must comply with:
- PACER Terms of Service
- Federal court access policies
- Attorney professional responsibility rules
- Client confidentiality requirements

This integration is for EDUCATIONAL and AUTHORIZED use only.
