# 🚀 Quick Fix Checklist - 50 Minute Action Plan

**Goal**: Get all 6 integrations working
**Time**: 50 minutes
**Difficulty**: Medium (mostly copy-paste)

---

## ⏱️ PHASE 1: EMAIL (10 minutes) 🔴 START HERE

### Step 1.1: Delete Corrupted Gmail Token
```bash
cd ~/PIA-CLAUDE
rm token.json
echo "✅ Deleted corrupted token"
```

### Step 1.2: Get Google Credentials
1. Open: https://console.cloud.google.com
2. Create/Select your project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download as JSON
6. Copy content to `credentials.json` in project root
7. Extract `client_id` and `client_secret`

### Step 1.3: Update .env File
```bash
# Edit .env and add/update these lines:
GOOGLE_CLIENT_ID=your_client_id_from_step_1.2.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_secret_from_step_1.2
```

### Step 1.4: Test Gmail
```bash
python3 << 'EOF'
from src.mcp_servers.gmail_mcp import GmailMCPServer
gmail = GmailMCPServer()
if gmail.authenticated:
    print("✅ GMAIL WORKING!")
    result = gmail.send_email("your_email@gmail.com", "Test", "This is a test email")
    print(f"✅ Email sent: {result}")
else:
    print("❌ Not authenticated - check browser OAuth flow")
EOF
```

**Expected**: Browser opens, you click "Allow", then returns credentials. Token saved automatically.

**Status Check**:
- ✅ `token.json` created?
- ✅ Can read email address?
- ✅ Send test email works?

---

## ⏱️ PHASE 2: QUICK WINS (5 minutes) 🟢

### Step 2.1: WhatsApp Setup
```bash
# Edit .env and add:
WHATSAPP_ACCESS_TOKEN=your_permanent_token_from_meta_business
WHATSAPP_PHONE_NUMBER_ID=your_phone_id_from_meta
TEST_WHATSAPP_PHONE=+447911123456  # Your phone number (E.164 format)
```

**Where to get tokens**:
- Meta Business Suite → WhatsApp Settings → API Setup
- Phone Number ID visible in WhatsApp section
- Generate permanent token (not temporary)

### Step 2.2: Test WhatsApp
```bash
python3 << 'EOF'
from src.mcp_servers.whatsapp_mcp_real import WhatsAppMCPServer
wa = WhatsAppMCPServer()
if wa.authenticated:
    result = wa.send_message("+447911123456", "Test from Zoya ✅")
    print(f"✅ WhatsApp ready: {result}")
else:
    print("❌ Check credentials")
EOF
```

---

## ⏱️ PHASE 3: SOCIAL MEDIA (35 minutes) 🟡

### Step 3.1: Twitter - 15 minutes

**3.1.1 - Regenerate Keys**
1. Open: https://developer.twitter.com/en/portal/dashboard
2. Select your App → Keys and tokens
3. Regenerate API Key and Secret (consumer keys)
4. Generate Access Token and Secret (if expired)
5. Copy all 4 values

**3.1.2 - Update .env**
```bash
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=optional_but_helpful
```

**3.1.3 - Test Twitter**
```bash
python3 << 'EOF'
from src.mcp_servers.twitter_mcp_real import TwitterMCPServer
tw = TwitterMCPServer()
if tw.authenticated:
    result = tw.post_tweet("Test tweet from Zoya AI ✅ #automation")
    print(f"✅ Tweet posted: {result}")
    # Verify at: https://twitter.com/your_handle
else:
    print("❌ Check API credentials")
EOF
```

---

### Step 3.2: Meta/Facebook - 10-15 minutes

**3.2.1 - Generate New Token**
1. Open: https://developers.facebook.com/apps/
2. Select your App
3. Go to: Tools → Graph API Explorer
4. Select your App and Page
5. In permission dropdown, search for:
   - `pages_manage_posts` ✅ Check
   - `pages_read_engagement` ✅ Check
6. Click "Generate Access Token"
7. Copy the token shown
8. Extend it to long-lived:
   ```
   https://graph.facebook.com/oauth/access_token?
   grant_type=fb_exchange_token
   &client_id=YOUR_APP_ID
   &client_secret=YOUR_APP_SECRET
   &fb_exchange_token=SHORT_TOKEN_FROM_STEP_6
   ```
9. Copy the `access_token` from response

**3.2.2 - Update .env**
```bash
META_ACCESS_TOKEN=your_long_lived_token
FACEBOOK_PAGE_ID=your_facebook_page_id  # if posting to page
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_id  # if using Instagram
```

**3.2.3 - Test Meta**
```bash
python3 << 'EOF'
from src.mcp_servers.meta_mcp_real import MetaMCPServer
meta = MetaMCPServer()
if meta.authenticated:
    # Test Facebook
    result = meta.post_to_facebook("Test post from Zoya ✅")
    print(f"✅ Facebook post: {result}")
else:
    print("❌ Check token")
EOF
```

---

### Step 3.3: LinkedIn - 10-20 minutes

**3.3.1 - Complete OAuth Flow**
1. Create OAuth URL:
   ```
   https://www.linkedin.com/oauth/v2/authorization?
   response_type=code
   &client_id=YOUR_LINKEDIN_CLIENT_ID
   &redirect_uri=http://localhost:8000/callback
   &scope=w_member_social,w_organization_social,r_organization_social
   ```
2. Open in browser, accept permissions
3. You'll be redirected with `code=ABC123...`
4. Copy the code

**3.3.2 - Exchange Code for Token**
```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=YOUR_CODE&client_id=YOUR_ID&client_secret=YOUR_SECRET&redirect_uri=http://localhost:8000/callback"
```

Copy the `access_token` from response

**3.3.3 - Get Your Page/Person URN**
```bash
# For company page:
curl -X GET https://api.linkedin.com/v2/organizationAcls \
  -H "Authorization: Bearer YOUR_TOKEN"

# For personal profile:
curl -X GET https://api.linkedin.com/v2/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Look for `id` field, e.g., `urn:li:organization:123456` or `urn:li:person:ABC123`

**3.3.4 - Update .env**
```bash
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_PAGE_ID=urn:li:organization:12345  # For company pages
# OR
LINKEDIN_PERSON_URN=urn:li:person:ABC123DEF  # For personal posts
```

**3.3.5 - Test LinkedIn**
```bash
python3 << 'EOF'
from src.mcp_servers.linkedin_mcp_real import LinkedInMCPServer
li = LinkedInMCPServer()
if li.authenticated:
    result = li.post_to_linkedin("Test post from Zoya AI ✅ #automation")
    print(f"✅ LinkedIn post: {result}")
else:
    print("❌ Check token and URN")
EOF
```

---

## ✅ PHASE 4: VERIFICATION (2 minutes)

### Step 4.1: Run Full Test Suite
```bash
cd ~/PIA-CLAUDE
python test_post_all_integrations.py
```

### Step 4.2: Expected Output
```
✅ Gmail: Connected & authenticated
✅ Twitter: Connected & authenticated
✅ LinkedIn: Connected & authenticated
✅ Meta/Facebook: Connected & authenticated
✅ WhatsApp: Connected & authenticated
✅ Odoo: Connected & authenticated

All tests passed! 🎉
```

### Step 4.3: Verify in UI
- Check Gmail inbox for test email
- Visit Twitter/X and see your test tweet
- Visit Facebook page and see your post
- Visit LinkedIn and see your post
- Check WhatsApp for test message
- Check Odoo for any created records

---

## 🔍 Troubleshooting

### Gmail Won't Authenticate
**Issue**: Browser doesn't open
```bash
# Manual OAuth:
# 1. Delete token.json
# 2. Run: python -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; GmailMCPServer()"
# 3. Watch for: "Please visit this URL to authorize this application"
# 4. Copy-paste URL into browser manually
```

### Twitter 401 Unauthorized
**Issue**: API keys don't work
```bash
# Check if using API v2:
# 1. Developer Dashboard → Settings → API setup
# 2. Should show v2 with "Essential" or higher tier
# 3. If v1.1, upgrade to v2
```

### LinkedIn Token Invalid
**Issue**: Token expired (65 day limit)
```bash
# Regenerate:
# 1. Start OAuth flow again (Section 3.3.1)
# 2. Save new token to .env
# 3. LinkedIn tokens expire every 65 days - plan to refresh
```

### Meta Token Session Invalid
**Issue**: User logged out
```bash
# Fix: Generate NEW long-lived token
# 1. Go to Graph API Explorer
# 2. Select correct App and Page
# 3. Generate fresh token
# 4. Update .env with new token
```

---

## 📋 Credential Checklist

Print this and check off as you complete each one:

- [ ] **Gmail**
  - [ ] `GOOGLE_CLIENT_ID` in .env
  - [ ] `GOOGLE_CLIENT_SECRET` in .env
  - [ ] `token.json` created
  - [ ] Test email sent successfully

- [ ] **WhatsApp**
  - [ ] `WHATSAPP_ACCESS_TOKEN` in .env
  - [ ] `WHATSAPP_PHONE_NUMBER_ID` in .env
  - [ ] `TEST_WHATSAPP_PHONE` in .env (E.164 format)
  - [ ] Test message sent successfully

- [ ] **Twitter**
  - [ ] `TWITTER_API_KEY` in .env
  - [ ] `TWITTER_API_SECRET` in .env
  - [ ] `TWITTER_ACCESS_TOKEN` in .env
  - [ ] `TWITTER_ACCESS_TOKEN_SECRET` in .env
  - [ ] Test tweet posted

- [ ] **Meta/Facebook**
  - [ ] `META_ACCESS_TOKEN` in .env (long-lived)
  - [ ] Scopes include: `pages_manage_posts`
  - [ ] `FACEBOOK_PAGE_ID` in .env (if needed)
  - [ ] Test post created on Facebook

- [ ] **LinkedIn**
  - [ ] `LINKEDIN_CLIENT_ID` in .env
  - [ ] `LINKEDIN_CLIENT_SECRET` in .env
  - [ ] `LINKEDIN_ACCESS_TOKEN` in .env
  - [ ] `LINKEDIN_PAGE_ID` OR `LINKEDIN_PERSON_URN` in .env
  - [ ] Test post created

- [ ] **Odoo**
  - [ ] Already working ✅

---

## ⏰ Time Breakdown

| Phase | Task | Time |
|-------|------|------|
| 1 | Gmail Setup | 5-10 min |
| 2 | WhatsApp Quick Win | 2 min |
| 3a | Twitter Keys | 15 min |
| 3b | Meta/Facebook Token | 10-15 min |
| 3c | LinkedIn OAuth | 10-20 min |
| 4 | Test & Verify | 2-5 min |
| **Total** | **Full Stack** | **44-67 min** |

**Fastest Path** (if you have all API access ready): **35-40 minutes**
**Realistic Path** (with finding credentials): **50-60 minutes**

---

## 🎯 Success Criteria

You'll know everything is working when:

1. ✅ All 6 services show "Authenticated" in logs
2. ✅ Test emails arrive in your inbox
3. ✅ Test tweets appear on Twitter/X
4. ✅ Test posts appear on LinkedIn
5. ✅ Test posts appear on Facebook
6. ✅ Test messages arrive on WhatsApp
7. ✅ Odoo shows connected status
8. ✅ NDJSON logs created in `AI_Employee_Vault/Logs/`
9. ✅ Files moving between vault folders atomically
10. ✅ No 401/403/expired token errors

---

## 🚨 Critical Notes

1. **Never commit .env to Git** - it has secrets!
2. **Keep API keys secure** - don't share in messages
3. **LinkedIn tokens expire every 65 days** - plan to refresh
4. **Twitter API v2 only** - v1.1 is deprecated
5. **Meta needs long-lived tokens** - not temporary ones
6. **WhatsApp needs E.164 format** - `+{country}{number}`
7. **Odoo is already working** - no action needed

---

## 💪 You've Got This!

Each step is straightforward. Focus on:
1. One service at a time
2. Copy-paste credentials carefully
3. Test immediately after each one
4. Check browser/API dashboards if stuck

Once you complete this checklist, you'll have a **fully operational production-ready system** with email, social media, and messaging working across 6 platforms!

**Start with Phase 1 now** 👇 Let me know when you hit any blockers!
