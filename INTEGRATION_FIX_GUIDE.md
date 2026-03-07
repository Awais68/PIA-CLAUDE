# Quick Integration Fix Guide

**Test Results**: 1 ✅ | 4 ❌ | 1 ⚠️ SKIP

**To Get All Integrations Working**: Follow steps 1-5 in order (40 minutes total)

---

## 1️⃣ GMAIL (5 minutes) - 🔴 CRITICAL

### Current Status
- ❌ Invalid OAuth scope error
- Needs re-authentication

### Fix
```bash
# Step 1: Delete corrupted token
rm token.json

# Step 2: Run the test again (will prompt for browser login)
python test_post_all_integrations.py

# It will open a browser → Click "Allow" to grant gmail.send permission
# Token automatically saved to token.json
```

### Verify
```bash
python -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; s = GmailMCPServer(); print('✅ OK' if s.authenticated else '❌ FAIL')"
```

---

## 2️⃣ WHATSAPP (2 minutes) - 🔴 CRITICAL

### Current Status
- ✅ Connected and working
- ⚠️ Needs TEST_WHATSAPP_PHONE configured

### Fix
Edit `.env` and add:
```
TEST_WHATSAPP_PHONE=+1234567890
```

Use your actual phone number in E.164 format:
- **USA**: `+12025551234`
- **UK**: `+442071234567`
- **India**: `+919876543210`
- **Other**: `+{country_code}{number}`

### Verify
```bash
python test_post_all_integrations.py
# Should show: "✅ WHATSAPP MESSAGE SENT"
```

---

## 3️⃣ TWITTER (15 minutes) - 🟠 HIGH

### Current Status
- ❌ 401 Unauthorized
- Invalid API credentials

### Fix
1. Go to: https://developer.twitter.com/en/portal/dashboard
2. Select your **Project** → **App**
3. Go to **Keys and tokens**
4. Generate/Regenerate:
   - API Key → copy to `.env` as `TWITTER_API_KEY`
   - API Secret → copy to `.env` as `TWITTER_API_SECRET`
   - Access Token → copy to `.env` as `TWITTER_ACCESS_TOKEN`
   - Access Token Secret → copy to `.env` as `TWITTER_ACCESS_TOKEN_SECRET`

### Verify
```bash
python -c "from src.mcp_servers.twitter_mcp_real import TwitterMCPServer; s = TwitterMCPServer(); print('✅ OK' if s.authenticated else '❌ FAIL')"
```

---

## 4️⃣ FACEBOOK / META (10 minutes) - 🟠 HIGH

### Current Status
- ❌ Token session invalid (error 190)
- User logged out or permissions changed

### Fix
1. Go to: https://developers.facebook.com/apps/
2. Select your app
3. **Settings** → **Basic** → Copy App ID
4. **Tools** → **Graph API Explorer**
5. Select your **App** (top left)
6. Select your **Page** (top middle)
7. Click **Generate Access Token**
8. Grant these permissions:
   - ✓ `pages_manage_posts`
   - ✓ `pages_read_engagement`
   - ✓ `page_events`
9. Select **Get Long-Lived Token** (60 days)
10. Copy token → `.env` as `META_ACCESS_TOKEN`
11. Also set `FACEBOOK_PAGE_ID` in `.env`

### Verify
```bash
python -c "from src.mcp_servers.meta_mcp_real import MetaMCPServer; s = MetaMCPServer(); print('✅ OK' if s.authenticated else '❌ FAIL')"
```

---

## 5️⃣ LINKEDIN (10 minutes) - 🟡 MEDIUM

### Current Status
- ❌ No valid access token
- Token may be expired (max 65 days)

### Fix
1. Go to: https://linkedin.com (login with your account)
2. Go to your app at: https://www.linkedin.com/developers/apps
3. Select your app
4. **Auth** → **Authorized redirect URLs** → verify set to `http://localhost:8000/`
5. **Credentials** → Copy **Client ID**
6. Build authorization URL:
   ```
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8000/&scope=w_member_social%20w_organization_social
   ```
7. Open URL in browser → Click **Allow**
8. You'll be redirected with `code=ABC123...` in URL
9. Use this tool to exchange code for token:
   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -d "grant_type=authorization_code&code=YOUR_CODE&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&redirect_uri=http://localhost:8000/"
   ```
10. Copy `access_token` from response → `.env` as `LINKEDIN_ACCESS_TOKEN`
11. Also set `LINKEDIN_PERSON_URN` (format: `urn:li:person:ABC123XYZ`)

### Verify
```bash
python -c "from src.mcp_servers.linkedin_mcp_real import LinkedInMCPServer; s = LinkedInMCPServer(); print('✅ OK' if s.authenticated else '❌ FAIL')"
```

---

## Final Verification

After completing all 5 steps, run:

```bash
python test_post_all_integrations.py
```

Expected output:
```
Total: 6 Passed | 0 Failed | 0 Skipped ✅
```

---

## Troubleshooting

### If test still shows errors after fixes:

1. **Check .env format**
   ```bash
   # Make sure no quotes around values
   TWITTER_API_KEY=abc123def456        ✅ CORRECT
   TWITTER_API_KEY="abc123def456"      ❌ WRONG
   ```

2. **Verify no spaces**
   ```bash
   # No spaces around =
   WHATSAPP_ACCESS_TOKEN=token123      ✅ CORRECT
   WHATSAPP_ACCESS_TOKEN = token123    ❌ WRONG
   ```

3. **Check .env is in right location**
   ```bash
   # Should be in project root
   ls -la .env
   # Output: -rw-r--r-- 1 awais awais ... .env
   ```

4. **Reload environment**
   ```bash
   # Python caches .env, so restart:
   python test_post_all_integrations.py
   ```

---

## Need Help?

Check detailed report:
```bash
cat TEST_RESULTS_2026_03_02.md
```

View full test logs:
```bash
python test_post_all_integrations.py 2>&1 | tee test_output.log
```

---

**Estimated Total Time**: ~40 minutes
**Difficulty**: Easy-Medium
**Success Rate**: ~95% (assuming valid credentials available)

Good luck! 🚀
