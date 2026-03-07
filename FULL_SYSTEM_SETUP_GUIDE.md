# Full Zoya System Setup Guide

Complete setup for all 6 platform integrations. Follow these steps in order.

---

## 📋 Setup Overview

| Platform | Time | Status | Setup File |
|----------|------|--------|-----------|
| LinkedIn (Playwright) | 5 min | ✅ Ready | `setup_linkedin_playwright.py` |
| Gmail (OAuth) | 10 min | ✅ Ready | `setup_gmail_oauth.py` |
| Twitter (API) | 15 min | ✅ Ready | `setup_twitter_api.py` |
| Meta/Facebook (API) | 10 min | ✅ Ready | `setup_meta_api.py` |
| WhatsApp (Local) | 5 min | ✅ Ready | `setup_whatsapp_local.py` |
| Odoo (Already Working) | 0 min | ✅ Done | (Already configured) |

**Total Time**: ~40 minutes

---

## Step-by-Step Setup

### ✅ Step 1: LinkedIn Setup (5 minutes)

LinkedIn uses **Playwright browser automation** - no tokens needed, just email + password.

```bash
cd ~/PIA-CLAUDE
python3 setup_linkedin_playwright.py
```

**What it does:**
1. Installs Playwright if needed
2. Asks for your LinkedIn email and password
3. Tests login and saves session
4. Verifies everything works

**Result:** `~/.linkedin_session/` folder created with your session

---

### ✅ Step 2: Gmail Setup (10 minutes)

Gmail uses **OAuth 2.0** - requires Google Cloud credentials file.

**Before running script:**

1. Go to: https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (select "Desktop application")
3. Download as `credentials.json`
4. Save to: `~/PIA-CLAUDE/credentials.json`

**Then run:**

```bash
cd ~/PIA-CLAUDE
python3 setup_gmail_oauth.py
```

**What it does:**
1. Checks for `credentials.json`
2. Removes any corrupted token
3. Opens browser for OAuth login
4. Tests Gmail connection
5. Verifies email access works

**Result:** `token.json` created (auto-refreshed by system)

---

### ✅ Step 3: Twitter Setup (15 minutes)

Twitter uses **API v1.1 + v2 Bearer Token**.

**Before running script:**

1. Go to: https://developer.twitter.com/en/portal/dashboard
2. Create or select an app
3. Go to "Keys and tokens" tab
4. Generate/copy these 5 keys:
   - API Key (Consumer Key)
   - API Secret Key (Consumer Secret)
   - Access Token
   - Access Token Secret
   - Bearer Token

**Then run:**

```bash
cd ~/PIA-CLAUDE
python3 setup_twitter_api.py
```

**What it does:**
1. Prompts you to enter all 5 keys
2. Saves them to `.env` (git-ignored)
3. Tests API connection
4. Verifies posting capability

**Result:** Twitter posting enabled in orchestrator

---

### ✅ Step 4: Meta/Facebook Setup (10 minutes)

Meta uses **Graph API** - requires business app credentials.

**Before running script:**

1. Go to: https://developers.facebook.com/
2. Create or select an app
3. Go to "Settings" → "Basic"
4. Get these credentials:
   - App ID
   - App Secret
   - Access Token (from "Tools" → "Access Token Tool")
5. Get your Facebook Page ID:
   - Go to your Facebook Page
   - Settings → Page Info → Find "Facebook Page ID"

**Then run:**

```bash
cd ~/PIA-CLAUDE
python3 setup_meta_api.py
```

**What it does:**
1. Prompts for all Meta credentials
2. Saves to `.env` (git-ignored)
3. Tests Graph API connection
4. Verifies Facebook + Instagram posting

**Result:** Meta/Facebook/Instagram posting enabled

---

### ✅ Step 5: WhatsApp Setup (5 minutes)

WhatsApp uses **Local Playwright** - no API keys, just QR code scan.

**What it does:**
1. Installs Playwright if needed
2. Opens browser to WhatsApp Web
3. Shows QR code
4. You scan with your phone
5. Saves session locally

**Run:**

```bash
cd ~/PIA-CLAUDE
python3 setup_whatsapp_local.py
```

**Result:** `~/.whatsapp_session/` folder created (session persists 30 days)

---

### ✅ Step 6: Odoo Status Check

Odoo is already configured and working. Verify it's still connected:

```bash
python3 << 'EOF'
from src.mcp_servers.odoo_mcp_real import OdooMCPServer
server = OdooMCPServer()
if server.authenticated:
    print("✅ Odoo is working - UID:", server.uid)
else:
    print("❌ Odoo connection failed")
EOF
```

---

## 🎯 Setup Completion Checklist

After all steps complete, verify everything:

```bash
# 1. Check .env has all credentials
echo "=== .env Configuration ==="
grep -E "LINKEDIN|GMAIL|TWITTER|META|WHATSAPP" .env | wc -l
echo "   Should see: ~20-25 environment variables"

# 2. Check session files exist
echo "=== Session Files ==="
ls -la ~/.linkedin_session/
ls -la ~/.whatsapp_session/

# 3. Check token files
echo "=== Token Files ==="
ls -la token.json credentials.json

# 4. Verify all services
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

services = [
    ("LinkedIn", "linkedin_playwright_login", "LinkedInPlaywrightLogin"),
    ("Gmail", "mcp_servers.gmail_mcp", "GmailMCPServer"),
    ("Twitter", "mcp_servers.twitter_mcp_real", "TwitterMCPServer"),
    ("Meta", "mcp_servers.meta_mcp_real", "MetaMCPServer"),
    ("Odoo", "mcp_servers.odoo_mcp_real", "OdooMCPServer"),
]

for name, module, cls in services:
    try:
        mod = __import__(module, fromlist=[cls])
        obj = getattr(mod, cls)()
        status = "✅" if hasattr(obj, 'authenticated') and obj.authenticated else "⏳"
        print(f"{status} {name}")
    except Exception as e:
        print(f"❌ {name}: {str(e)[:30]}")
EOF
```

---

## 📁 Your System After Setup

```
~/PIA-CLAUDE/
├── .env                          ← All credentials (git-ignored ✅)
├── token.json                    ← Gmail OAuth token
├── credentials.json              ← Gmail OAuth client secrets
├── setup_linkedin_playwright.py  ← LinkedIn setup (complete ✅)
├── setup_gmail_oauth.py          ← Gmail setup (complete ✅)
├── setup_twitter_api.py          ← Twitter setup (complete ✅)
├── setup_meta_api.py             ← Meta setup (complete ✅)
├── setup_whatsapp_local.py       ← WhatsApp setup (complete ✅)
├── AI_Employee_Vault/            ← Your vault (files to process)
├── Logs/                         ← Orchestrator logs
└── src/
    ├── mcp_servers/              ← API clients (ready to use)
    ├── local_agent/              ← Local processing
    └── cloud_agent/              ← Cloud orchestrator

~/.linkedin_session/              ← LinkedIn session (persistent)
~/.whatsapp_session/              ← WhatsApp session (persistent)
```

---

## 🚀 Your First Posts

After setup, test each platform:

### Test LinkedIn Post

Create file: `AI_Employee_Vault/Pending_Approval/social/LINKEDIN_TEST.md`

```markdown
---
type: linkedin
status: pending
platforms: [linkedin]
created_at: 2026-03-05T14:30:00Z
---

Testing LinkedIn! 🚀

If you see this, Playwright is working perfectly!

#automation #ai
```

### Test Twitter Post

Create file: `AI_Employee_Vault/Pending_Approval/social/TWITTER_TEST.md`

```markdown
---
type: twitter
status: pending
platforms: [twitter]
created_at: 2026-03-05T14:30:00Z
---

Testing Twitter API! 🐦

If you see this, Twitter integration is working!

#automation #ai
```

### Test Gmail

Create file: `AI_Employee_Vault/Needs_Action/EMAIL_TEST_20260305.md`

```markdown
---
type: email
status: pending
to: your-email@example.com
subject: Zoya System Test
created_at: 2026-03-05T14:30:00Z
---

Testing Gmail integration!

If you received this, email is working.
```

### Test Meta/Facebook

Create file: `AI_Employee_Vault/Pending_Approval/social/FACEBOOK_TEST.md`

```markdown
---
type: facebook
status: pending
platforms: [facebook]
created_at: 2026-03-05T14:30:00Z
---

Testing Meta API! 📘

If you see this, Facebook is working!

#automation #ai
```

### Test WhatsApp

Create file: `AI_Employee_Vault/Pending_Approval/social/WHATSAPP_TEST_20260305.md`

```markdown
---
type: whatsapp
status: pending
to: +1234567890
created_at: 2026-03-05T14:30:00Z
---

Testing WhatsApp! 💬

If you got this message, WhatsApp is working!
```

---

## ⚡ Quick Commands Reference

```bash
# Test all services at once
python3 test_post_all_integrations.py

# Check specific service
python3 -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; print('✅ Gmail' if GmailMCPServer().authenticated else '❌ Gmail')"

# View logs
tail -f Logs/2026-03-05.json

# Check vault queue
ls -la AI_Employee_Vault/Pending_Approval/social/
ls -la AI_Employee_Vault/Needs_Action/

# Run orchestrator manually
python3 src/cloud_agent/orchestrator.py

# Check system health
python3 src/cloud_agent/health_monitor.py
```

---

## 🔐 Security Checklist

✅ **Do:**
- [ ] Keep `.env` file safe (never commit)
- [ ] Use strong, unique passwords
- [ ] Store credentials file (credentials.json) securely
- [ ] Review `.gitignore` before committing

❌ **Don't:**
- [ ] Commit `.env` or credentials to Git
- [ ] Share credentials in messages
- [ ] Reuse passwords across services
- [ ] Log credentials in error messages

---

## 🆘 If Something Goes Wrong

### LinkedIn Won't Connect

```bash
# Reset and try again
rm -rf ~/.linkedin_session/
python3 setup_linkedin_playwright.py
```

### Gmail Token Expired

```bash
# Reset OAuth
rm token.json
python3 setup_gmail_oauth.py
```

### Twitter API Fails

```bash
# Verify keys in .env
grep TWITTER .env

# Check Developer Dashboard for key issues
# Regenerate if needed and update .env
```

### WhatsApp Session Expired

```bash
# Reset and re-login
rm -rf ~/.whatsapp_session/
python3 setup_whatsapp_local.py
```

### General Troubleshooting

```bash
# Check what's in .env
cat .env | grep -v "^#" | grep -v "^$"

# Verify Python imports work
python3 -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; print('✅')"

# Check logs for errors
grep "error" Logs/*.json | tail -10

# Test with small file
echo "Test" > AI_Employee_Vault/Pending_Approval/test.txt
# Should move to Done/ after 30 seconds
```

---

## 📊 Next: Dashboard (Optional)

After all 6 platforms work, optionally set up the web dashboard:

```bash
cd vault-control
npm install
npm run dev
```

Then open: http://localhost:3000

Dashboard shows:
- Live stats from all platforms
- Pending approvals
- Message threads
- System health
- Log viewer

---

## ✨ You're Done!

All 6 platforms are now configured:

✅ **LinkedIn** - Playwright (simple, local)
✅ **Gmail** - OAuth (official Google API)
✅ **Twitter** - API (official Twitter API)
✅ **Meta/Facebook** - Graph API (official Meta API)
✅ **WhatsApp** - Local browser (no cloud API)
✅ **Odoo** - Already working

Your Zoya system is now fully integrated! 🚀

**Next time you need to:**
- Post to social media → Create `.md` file in `Pending_Approval/social/`
- Send email → Create `.md` file in `Needs_Action/`
- Any task → Create file, orchestrator processes it automatically

**Everything is automated and watched.** Just create files and the system handles the rest!

---

**Questions?** Check the individual setup files:
- `LINKEDIN_PLAYWRIGHT_SETUP.md`
- `BACKEND_INTEGRATION_ANALYSIS.md`
- `QUICK_FIX_CHECKLIST.md`
