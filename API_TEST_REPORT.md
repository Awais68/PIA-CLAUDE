# 🧪 API Integration Test Report
**Date**: 2026-03-01
**Status**: ⚠️ Partial Success (1/5 services ready)

---

## Executive Summary

### Test Results
| Service | Status | Issue | Priority |
|---------|--------|-------|----------|
| 📧 Gmail | ❌ Fail | Invalid scope in credentials.json | 🔴 High |
| 🐦 Twitter | ❌ Fail | OAuth keys not properly configured | 🔴 High |
| 💼 LinkedIn | ❌ Fail | 403 Forbidden (token expired/revoked) | 🔴 High |
| 📘 Facebook/Meta | ❌ Fail | Token expired or invalid | 🔴 High |
| 📋 Odoo | ✅ Pass | Connected successfully | 🟢 Ready |
| 💬 WhatsApp | ⚠️ Partial | Token configured but missing TEST_WHATSAPP_PHONE | 🟡 Medium |

---

## Detailed Test Results

### 1. Gmail API ❌
**Error**: `invalid_scope: Bad Request`
```
Gmail authentication failed: ('invalid_scope: Bad Request',
  {'error': 'invalid_scope', 'error_description': 'Bad Request'})
```

**Root Cause**:
- credentials.json has wrong/missing scopes
- Currently only has `gmail.send` scope
- Need to regenerate credentials with proper OAuth scopes

**Fix Steps** (15 minutes):
```bash
1. Delete old credentials:
   rm credentials.json token.json

2. Run Gmail OAuth setup:
   python -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; GmailMCPServer()"

3. Follow browser prompts to grant full Gmail access

4. Verify:
   python test_api_connectivity.py
```

---

### 2. Twitter API ❌
**Error**: `Consumer key must be string or bytes, not NoneType`
```
Tweepy trying to use OAuth keys that are:
- TWITTER_API_KEY = "b45l2u37ggE0dKxnR5Vm8jroN" ✅
- TWITTER_API_SECRET = "ofUNituXJCLVWBh41C1JIYv4tjv81LQNVL9TS5C3b9iRu" ✅
- But also requires TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_TOKEN_SECRET
```

**Root Cause**:
- .env has TWITTER_ACCESS_TOKEN = "For @The5217Code" (NOT valid token)
- Missing TWITTER_ACCESS_TOKEN_SECRET entirely

**Fix Steps** (10 minutes):
```bash
1. Get your actual access tokens from Twitter Dev Portal:
   https://developer.twitter.com/en/portal/dashboard

2. Update .env:
   TWITTER_ACCESS_TOKEN=<actual_token>
   TWITTER_ACCESS_TOKEN_SECRET=<actual_secret>

3. Alternatively, use Bearer token only (already present):
   TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAHOw7wE... ✅

4. Run with Bearer token test:
   python -c "import tweepy; c=tweepy.Client(bearer_token='...'); print(c.get_me())"
```

---

### 3. LinkedIn API ❌
**Error**: `403 Forbidden`
```
Status Code: 403
Likely causes:
- Token expired (90-day limit)
- Insufficient permissions
- Wrong scope requested
```

**Root Cause**:
- Access token may have expired (was set 2026-02-25, now 2026-03-01)
- Or token was revoked by LinkedIn

**Fix Steps** (20 minutes):
```bash
1. Refresh token via LinkedIn OAuth:
   python -c "
   from src.linkedin_poster import refresh_linkedin_token()
   "

2. Or use Playwright browser auth (preferred):
   python linkedin_playwright_login.py
   - Opens browser
   - Log in to LinkedIn
   - Automatically extracts new token

3. Update .env with new token:
   LINKEDIN_ACCESS_TOKEN=<new_token>

4. Verify:
   python test_api_connectivity.py
```

---

### 4. Facebook/Meta API ❌
**Error**: `400 Bad Request`
```
Meta Graph API returned 400
Likely causes:
- Token expired
- Insufficient scopes (need pages_manage_posts)
- Invalid page ID
```

**Root Cause**:
- Facebook token may have expired
- May need pages_manage_posts scope

**Fix Steps** (15 minutes):
```bash
1. Regenerate token with correct scopes:
   - Go to Facebook Developers: https://developers.facebook.com
   - App → Settings → Basic
   - Select "pages_manage_posts" scope
   - Generate new token

2. Update .env:
   META_ACCESS_TOKEN=<new_token>
   FACEBOOK_ACCESS_TOKEN=<new_token>

3. Verify page ID is correct:
   FACEBOOK_PAGE_ID=122101733007271133

4. Test:
   python test_api_connectivity.py
```

---

### 5. Odoo XML-RPC API ✅
**Status**: WORKING!
```
✅ Odoo authenticated successfully
   User ID: 2
```

**Next Steps**:
- Already connected and ready
- Can create invoices and manage data
- No action needed

---

### 6. WhatsApp Cloud API ⚠️
**Status**: Configured but incomplete
```
✅ Token: Configured
✅ Phone ID: Configured
✅ Business ID: Configured
❌ TEST_WHATSAPP_PHONE: Missing
```

**Fix Steps** (5 minutes):
```bash
1. Add to .env:
   TEST_WHATSAPP_PHONE=+92XXXXXXXXXX  # Your WhatsApp number (E.164 format)

2. Test:
   python test_api_connectivity.py
```

---

## What Was Fixed ✅

| Fix | Status |
|-----|--------|
| Gmail token.json JSON format (not pickle) | ✅ Fixed in last commit |
| Twitter Bearer token added | ✅ Already in .env |
| LinkedIn Playwright support added | ✅ Client code updated |
| WhatsApp local MCP client | ✅ Implementation complete |
| Configuration structure | ✅ Ready |

---

## Quick Action Plan

### Immediate (30 minutes)
- [ ] Fix Gmail OAuth scopes - DELETE credentials.json & re-authenticate
- [ ] Fix Twitter - Add missing ACCESS_TOKEN and SECRET
- [ ] Add TEST_WHATSAPP_PHONE to .env

### Short-term (1 hour)
- [ ] Refresh LinkedIn token (use Playwright or OAuth refresh)
- [ ] Regenerate Facebook/Meta token with proper scopes
- [ ] Verify all tokens work: `python test_api_connectivity.py`

### Verification
```bash
# Run after fixes
python test_api_connectivity.py

# Run full integration test
python run_real_api_test.py
```

---

## Commands to Run Now

```bash
# 1. Check detailed configuration
python test_integration_detailed.py

# 2. Test real connectivity
python test_api_connectivity.py

# 3. Fix Gmail (delete old creds)
rm credentials.json token.json
python -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; GmailMCPServer()"

# 4. Test Twitter Bearer token
python -c "
import tweepy, os
from dotenv import load_dotenv
load_dotenv()
client = tweepy.Client(bearer_token=os.getenv('TWITTER_BEARER_TOKEN'))
print('Twitter User:', client.get_me().data.username)
"

# 5. Test LinkedIn (might work with refresh)
python linkedin_playwright_login.py  # Browser-based login

# 6. Full integration test (after fixes)
python run_real_api_test.py
```

---

## Success Criteria

- ✅ Gmail: Can send test email
- ✅ Twitter: Can post tweet
- ✅ LinkedIn: Can post content
- ✅ Facebook: Can post to page
- ✅ WhatsApp: Can send message
- ✅ Odoo: Can create invoice

**Current Status**: 1/6 ready (Odoo)
**Estimated time to fix all**: 1-2 hours

---

## Notes
- All credential formats look valid in .env
- Token expiration is the main issue (LinkedIn, Facebook)
- Gmail scope issue is fixable by re-authenticating
- Twitter needs OAuth token pair (has Bearer token which is alternative)
- Odoo is ready to go!
