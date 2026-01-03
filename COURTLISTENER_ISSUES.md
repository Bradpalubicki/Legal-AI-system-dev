# CourtListener API Issues - Troubleshooting Guide

## Current Issue
The CourtListener API (www.courtlistener.com) is experiencing connectivity issues from your network.

### Symptoms
- Search requests timeout after 60 seconds
- Error: "CourtListener API is currently unavailable or very slow"
- Main site returns 403 Forbidden
- API endpoints don't respond

## Root Cause
One of the following:
1. **CourtListener Service Issues**: The API may be experiencing downtime or high load
2. **Network Blocking**: Your ISP/firewall may be blocking CourtListener
3. **Rate Limiting**: Too many requests from your IP address
4. **Geographic Restrictions**: CourtListener may block certain regions

## Solutions

### Option 1: Wait and Retry (Recommended)
CourtListener may come back online shortly. Try again in 5-10 minutes.

### Option 2: Check Service Status
Visit https://www.courtlistener.com in your browser to verify:
- If it loads → Network/API issue
- If it shows 403 → Blocking/restriction issue
- If it doesn't load → Service down

### Option 3: Get a CourtListener API Key
1. Go to https://www.courtlistener.com/sign-in/
2. Create a free account
3. Get your API key from your account settings
4. Add to `.env` file:
   ```
   COURTLISTENER_API_KEY=your_key_here
   ```
5. Restart the backend server

**Benefits of API key:**
- Higher rate limits (5,000 requests/hour vs 100/hour)
- Better stability
- Priority access

### Option 4: Use PACER Instead
The app supports PACER integration which may work when CourtListener is down:
1. Go to the PACER section in the app
2. Enter your PACER credentials
3. Search for cases through PACER

**Note**: PACER requires an account and charges fees ($0.10/page)

### Option 5: Check Your Network
If the issue persists, check if your network is blocking CourtListener:

```bash
# Test connectivity
curl -v https://www.courtlistener.com

# Check if API is reachable
curl -v "https://www.courtlistener.com/api/rest/v4/search/?type=r&q=test&page=1"
```

If these fail, contact your network administrator or try:
- Different network (mobile hotspot, different WiFi)
- VPN service
- Different device

## What We've Done
1. ✅ Increased API timeout from 30s → 60s
2. ✅ Added better error messages
3. ✅ Changed error code from 400 → 503 (Service Unavailable)
4. ✅ Added fallback suggestions in error messages

## For Developers
Current timeout settings in `backend/app/src/services/courtlistener_service.py`:
```python
self.timeout = httpx.Timeout(60.0, connect=15.0)
```

To adjust, edit line 82 in the file above.

## Need Help?
If this issue persists for more than 24 hours:
1. Check CourtListener's Twitter/status page
2. Contact CourtListener support
3. File an issue at https://github.com/freelawproject/courtlistener/issues
