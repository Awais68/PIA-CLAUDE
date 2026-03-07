# Setup Quick Reference

Copy-paste commands for all 6 platform setups.

---

## One-Time Setup (Run All 5 Commands)

```bash
cd ~/PIA-CLAUDE

# 1. LinkedIn (5 min)
python3 setup_linkedin_playwright.py

# 2. Gmail (10 min) - requires credentials.json from Google Cloud
python3 setup_gmail_oauth.py

# 3. Twitter (15 min) - requires API keys from Twitter Developer Dashboard
python3 setup_twitter_api.py

# 4. Meta/Facebook (10 min) - requires credentials from Meta Developer
python3 setup_meta_api.py

# 5. WhatsApp (5 min) - scan QR code with your phone
python3 setup_whatsapp_local.py
```

**Total Time: ~40 minutes**

---

## Verify Everything Works

```bash
# Quick test - all services at once
python3 test_post_all_integrations.py

# Or test individually:
python3 -c "from src.mcp_servers.gmail_mcp import GmailMCPServer; print('✅ Gmail' if GmailMCPServer().authenticated else '❌')"
python3 -c "from src.mcp_servers.twitter_mcp_real import TwitterMCPServer; print('✅ Twitter' if TwitterMCPServer().authenticated else '❌')"
python3 -c "from src.mcp_servers.meta_mcp_real import MetaMCPServer; print('✅ Meta' if MetaMCPServer().authenticated else '❌')"
python3 -c "from linkedin_playwright_login import LinkedInPlaywrightLogin; print('✅ LinkedIn')"
python3 -c "from src.mcp_servers.odoo_mcp_real import OdooMCPServer; print('✅ Odoo' if OdooMCPServer().authenticated else '❌')"
```

---

## If Credentials Need Refreshing

```bash
# LinkedIn - reset session
rm -rf ~/.linkedin_session/
python3 setup_linkedin_playwright.py

# Gmail - reset OAuth token
rm token.json
python3 setup_gmail_oauth.py

# Twitter - get new API keys
python3 setup_twitter_api.py

# Meta - get new access token
python3 setup_meta_api.py

# WhatsApp - reset QR session
rm -rf ~/.whatsapp_session/
python3 setup_whatsapp_local.py
```

---

## Start Sending Messages

```bash
# Create LinkedIn post
cat > AI_Employee_Vault/Pending_Approval/social/LINKEDIN_HELLO.md << 'EOF'
---
type: linkedin
status: pending
platforms: [linkedin]
created_at: 2026-03-05T14:30:00Z
---

Hello from Zoya! 🚀
EOF

# Create Twitter post
cat > AI_Employee_Vault/Pending_Approval/social/TWITTER_HELLO.md << 'EOF'
---
type: twitter
status: pending
platforms: [twitter]
created_at: 2026-03-05T14:30:00Z
---

Hello from Zoya! 🐦
EOF

# Create email
cat > AI_Employee_Vault/Needs_Action/EMAIL_TEST.md << 'EOF'
---
type: email
to: your-email@example.com
subject: Test from Zoya
created_at: 2026-03-05T14:30:00Z
---

Testing email from Zoya!
EOF

# Create Facebook post
cat > AI_Employee_Vault/Pending_Approval/social/FACEBOOK_HELLO.md << 'EOF'
---
type: facebook
status: pending
platforms: [facebook]
created_at: 2026-03-05T14:30:00Z
---

Hello from Zoya! 📘
EOF

# Watch for results (every 30 seconds, orchestrator processes files)
watch -n 5 'ls -la AI_Employee_Vault/Done/ | tail -5'
```

---

## View Logs

```bash
# Latest activity
tail -50 Logs/$(date +%Y-%m-%d).json

# Follow logs in real-time
tail -f Logs/$(date +%Y-%m-%d).json

# Search for errors
grep "error" Logs/*.json | tail -20

# Search for specific service
grep "twitter" Logs/*.json

# Count by type
grep "action_type" Logs/*.json | cut -d: -f2 | sort | uniq -c
```

---

## Check Configuration

```bash
# Show all credentials (REDACTED)
grep -E "LINKEDIN|GMAIL|TWITTER|META|WHATSAPP" .env

# Show non-secret parts
grep -E "CLIENT_ID|PAGE_ID|PERSON_URN|ACCOUNT_ID" .env

# Check file permissions
ls -la .env token.json credentials.json 2>/dev/null
```

---

## Restart Orchestrator

```bash
# If orchestrator crashed, restart it
python3 src/cloud_agent/orchestrator.py &

# Check if running
ps aux | grep orchestrator

# Kill if needed
pkill -f "orchestrator.py"
```

---

## Dashboard (Optional)

```bash
# Install and start dashboard
cd vault-control
npm install
npm run dev

# Then open: http://localhost:3000
```

---

## Emergency Reset (If Everything Broken)

```bash
# Save your vault first!
cp -r AI_Employee_Vault ~/backup_vault_$(date +%s)/

# Remove all credentials (except .env content)
rm token.json credentials.json
rm -rf ~/.linkedin_session/
rm -rf ~/.whatsapp_session/

# Clear logs to start fresh
rm Logs/*.json

# Run full setup again
python3 setup_linkedin_playwright.py
python3 setup_gmail_oauth.py
python3 setup_twitter_api.py
python3 setup_meta_api.py
python3 setup_whatsapp_local.py

# Verify
python3 test_post_all_integrations.py
```

---

## What Each Platform Needs

| Platform | Setup Time | Requirements |
|----------|----------|--------------|
| **LinkedIn** | 5 min | Email + Password |
| **Gmail** | 10 min | credentials.json from Google Cloud |
| **Twitter** | 15 min | 4 API keys from Twitter Developer |
| **Meta/Facebook** | 10 min | App ID, Secret, Token, Page ID |
| **WhatsApp** | 5 min | Your phone + WhatsApp app |
| **Odoo** | 0 min | Already configured |

---

## File Locations Reference

```bash
# Setup Scripts
~/PIA-CLAUDE/setup_linkedin_playwright.py
~/PIA-CLAUDE/setup_gmail_oauth.py
~/PIA-CLAUDE/setup_twitter_api.py
~/PIA-CLAUDE/setup_meta_api.py
~/PIA-CLAUDE/setup_whatsapp_local.py

# Credentials
~/PIA-CLAUDE/.env              ← All secrets (NEVER commit)
~/PIA-CLAUDE/token.json        ← Gmail OAuth token
~/PIA-CLAUDE/credentials.json  ← Gmail OAuth secrets

# Sessions
~/.linkedin_session/           ← LinkedIn browser session
~/.whatsapp_session/           ← WhatsApp browser session

# Vault
~/PIA-CLAUDE/AI_Employee_Vault/
├── Pending_Approval/social/   ← Posts waiting to go live
├── Needs_Action/              ← Emails waiting approval
├── Approved/                  ← Approved items
├── Done/                      ← Processed items
└── Logs/                      ← Activity logs
```

---

## Need Help?

**For setup issues:**
- `FULL_SYSTEM_SETUP_GUIDE.md` - Complete step-by-step guide
- `BACKEND_INTEGRATION_ANALYSIS.md` - Technical details
- `QUICK_FIX_CHECKLIST.md` - Quick troubleshooting

**For platform-specific help:**
- LinkedIn: `LINKEDIN_PLAYWRIGHT_SETUP.md`
- Gmail: See `setup_gmail_oauth.py` troubleshooting section
- Twitter: See `setup_twitter_api.py` troubleshooting section
- Meta: See `setup_meta_api.py` troubleshooting section
- WhatsApp: See `setup_whatsapp_local.py` troubleshooting section

---

**That's it! You're ready to go.** 🚀
