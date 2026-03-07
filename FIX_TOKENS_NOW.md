# 🚀 Fix Tokens in 30 Minutes

## Current Status
- ✅ Odoo: WORKING
- ❌ Gmail: invalid_scope
- ❌ Twitter: Missing OAuth tokens
- ❌ LinkedIn: 403 Forbidden (expired)
- ❌ Facebook: 400 Bad Request (expired)
- ⚠️ WhatsApp: Missing TEST_WHATSAPP_PHONE

---

## 1. Gmail Fix (5 minutes)

### Problem
`invalid_scope: Bad Request` - credentials.json has wrong scopes

### Solution
```bash
# Delete old credentials
rm credentials.json token.json

# Regenerate (will open browser)
python -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; GmailMCPServer()"

# Follow the browser prompts to log in to your Gmail account
# Accept all permissions
# New token will be saved as token.json (JSON format)

# Test
python -c "
from src.mcp_servers.gmail_mcp import GmailMCPServer
g = GmailMCPServer()
if g.service: print('✅ Gmail is ready')
"
```

---

## 2. Twitter Fix (5 minutes)

### Problem
- Current `.env` has invalid ACCESS_TOKEN value: "For @The5217Code"
- Missing TWITTER_ACCESS_TOKEN_SECRET entirely
- Solution: Use existing Bearer token instead

### Solution A: Use Bearer Token (RECOMMENDED - Already Works!)
```bash
# Bearer token is already in .env and valid!
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAHOw7wE...

# Test it:
python -c "
import tweepy, os
from dotenv import load_dotenv
load_dotenv()
bearer = os.getenv('TWITTER_BEARER_TOKEN')
client = tweepy.Client(bearer_token=bearer)
user = client.get_me()
print(f'✅ Twitter ready as: {user.data.username}')
"
```

### Solution B: Fix OAuth Tokens (If Needed)
```bash
# Get from Twitter Developer Portal:
# https://developer.twitter.com/en/portal/dashboard

# Update .env:
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Test:
python test_api_connectivity.py
```

---

## 3. LinkedIn Fix (10 minutes)

### Problem
403 Forbidden - Token expired or insufficient permissions

### Solution A: Browser-Based Login (RECOMMENDED)
```bash
# Install Playwright first (if not already)
pip install playwright

# Run browser login
python linkedin_playwright_login.py

# This will:
# 1. Open browser
# 2. You log in to LinkedIn
# 3. Script extracts and saves new token
# 4. Automatically updates .env

# Test
python -c "
import requests, os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('LINKEDIN_ACCESS_TOKEN')
headers = {'Authorization': f'Bearer {token}'}
r = requests.get('https://api.linkedin.com/v2/me', headers=headers)
print('✅ LinkedIn ready' if r.status_code == 200 else f'❌ {r.status_code}')
"
```

### Solution B: Manual Token Refresh
```bash
# Go to LinkedIn Developer: https://www.linkedin.com/developers
# 1. Select your app
# 2. Go to "Auth" tab
# 3. Generate new access token
# 4. Copy and paste into .env:

LINKEDIN_ACCESS_TOKEN=your_new_token_here
LINKEDIN_CLIENT_ID=77qjb2drvnwbsc
LINKEDIN_PERSON_URN=urn:li:person:JFkdUz5Dwg
```

---

## 4. Facebook/Meta Fix (10 minutes)

### Problem
400 Bad Request - Token expired or invalid scope

### Solution
```bash
# Get new token from Meta/Facebook Developer:
# https://developers.facebook.com

# Steps:
# 1. Go to your app
# 2. Tools → Access Token Debugger
# 3. Check if your token is expired
# 4. If yes, go to "Settings" and regenerate token
# 5. IMPORTANT: Ensure scope includes "pages_manage_posts"

# Update .env:
META_ACCESS_TOKEN=EAAa47R... (new token)
FACEBOOK_ACCESS_TOKEN=EAAa47R... (same or different)

# Verify page ID is correct:
FACEBOOK_PAGE_ID=122101733007271133

# Test
python -c "
import requests, os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('META_ACCESS_TOKEN')
r = requests.get('https://graph.facebook.com/v18.0/me',
                 params={'access_token': token})
print('✅ Meta ready' if r.status_code == 200 else f'❌ {r.status_code}')
"
```

---

## 5. WhatsApp Fix (2 minutes)

### Problem
Missing TEST_WHATSAPP_PHONE environment variable

### Solution
```bash
# Add to .env:
TEST_WHATSAPP_PHONE=+923352204606

# Use E.164 format: +[country code][number]
# Examples:
# +923352204606  (Pakistan)
# +14155552671   (USA)
# +442071838750  (UK)

# Test
python test_api_connectivity.py
```

---

## Test Everything

```bash
# After all fixes:
python test_api_connectivity.py

# Expected output:
# ✅ Gmail: Connected
# ✅ Twitter: Connected
# ✅ LinkedIn: Connected
# ✅ Facebook: Connected
# ✅ Odoo: Connected ← Already working

# Then run full integration test:
python run_real_api_test.py
```

---

## Fastest Path (15 minutes for 5 services)

```bash
# 1. Gmail (5 min)
rm credentials.json token.json
python -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; GmailMCPServer()"

# 2. Twitter (1 min)
# Already has Bearer token - no fix needed!
# Just use: TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAHOw7wE...

# 3. LinkedIn (5 min)
python linkedin_playwright_login.py
# Scan browser QR/login

# 4. Facebook (3 min)
# Manually update .env with new token from developer portal

# 5. WhatsApp (1 min)
# Add TEST_WHATSAPP_PHONE to .env

# 6. Verify
python test_api_connectivity.py
```

---

## If You Stuck

### Gmail still failing?
```bash
rm -rf ~/.cache/google-auth-oauthlib
rm credentials.json token.json
python -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; GmailMCPServer()"
```

### Twitter still failing?
```bash
# Check Bearer token format
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('TWITTER_BEARER_TOKEN')
print(f'Bearer token starts with: {token[:20]}...')
print(f'Valid format: {token.startswith(\"AAAA\")}')"
```

### LinkedIn still 403?
```bash
# Token definitely expired, must refresh
python linkedin_playwright_login.py
# Or manually get from developer portal
```

### Facebook still 400?
```bash
# Check token in debugger
# https://developers.facebook.com/tools/debug/accesstoken

# If expired, generate new one with these scopes:
# - pages_manage_posts
# - pages_read_engagement
# - instagram_basic
# - instagram_manage_insights
```

---

**Estimated Time**: 15-30 minutes
**Success Criteria**: All tests pass in `python test_api_connectivity.py`
