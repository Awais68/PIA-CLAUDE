# Zoya Gold Tier — Quick Start Guide

**Last Updated:** 2026-02-24

---

## ⚡ 30-Second Setup

```bash
# 1. Install dependencies
uv sync

# 2. Start all services (one command)
bash scripts/start_gold.sh

# 3. In another terminal, drop a test file
cp ~/Documents/test.pdf AI_Employee_Vault/Inbox/

# 4. Watch it process in real-time
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).log
```

**That's it.** The system is now running. Check the dashboard anytime:

```bash
cat AI_Employee_Vault/Dashboard.md
```

---

## 📋 What Happens When You Drop a File

1. **Watcher detects** (2-3 seconds)
   - Validates file type
   - Computes SHA-256 hash (checks for duplicates)
   - Waits for file stability

2. **Queues to Needs_Action** (automatic)
   - Creates metadata .md file with timestamp

3. **Orchestrator claims** (next polling cycle, ~5 seconds)
   - Moves to In_Progress (atomic operation)
   - Prevents race conditions

4. **AI processes** (30-60 seconds depending on file size)
   - Reads document
   - Generates summary
   - Extracts action items
   - Categorizes (invoice, contract, proposal, note, etc.)
   - Assigns priority (high/medium/low)
   - Writes results to metadata

5. **Routes based on type**
   - **Automatic:** Low-priority items → Done/
   - **HITL Approval:** High-priority invoices/contracts → Pending_Approval/
   - **Failed:** Max retries reached → Quarantine/

6. **Dashboard updates** (automatic after each batch)

---

## 🎯 Common Workflows

### Post to LinkedIn

```bash
# 1. Create a post file (or use existing)
# AI_Employee_Vault/Pending_Approval/LINKEDIN_*.md already created

# 2. Approve it (move to Approved/)
mv AI_Employee_Vault/Pending_Approval/LINKEDIN_*.md AI_Employee_Vault/Approved/

# 3. Social Media Daemon posts within 5 minutes
# Check logs:
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).log | grep linkedin
```

### Schedule a Tweet

```bash
# 1. Open Tweet Queue
vim AI_Employee_Vault/Business/Tweet_Queue.md

# 2. Add a line:
# - [ ] scheduled_for: 2026-02-25 10:00 UTC | Your tweet here #hashtag

# 3. Save. The daemon will:
#    - Create approval request at scheduled time
#    - Post when approved
#    - Mark as [x] when done
```

### Generate Briefing

```bash
# Daily briefing
uv run zoya-briefing

# Weekly briefing (comprehensive)
uv run zoya-briefing --weekly

# Output: AI_Employee_Vault/Briefings/BRIEFING_*.md
```

### Check System Health

```bash
# Ralph Wiggum diagnostics
uv run zoya-ralph

# Output example:
# System Health: 50/100 (WARNING)
# Issues:
# - 17 items pending approval (age: 1-4 days)
# - 4 items stuck in In_Progress
```

---

## 🔧 Configuration

All settings via environment variables in `.env`:

```bash
# AI Provider (what processes documents)
AI_PROVIDER=claude              # options: claude, qwen, ollama

# Gmail (OAuth 2.0)
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...

# LinkedIn (API v2)
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_PAGE_ID=...
LINKEDIN_DRY_RUN=false         # Set to false to actually post

# Twitter/X (OAuth 1.0a via Tweepy)
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
TWITTER_DRY_RUN=false          # Set to false to actually tweet

# WhatsApp (Meta Business API)
WHATSAPP_API_URL=https://graph.instagram.com/v18.0
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_BUSINESS_ACCOUNT_ID=...
WHATSAPP_ACCESS_TOKEN=...
```

**For first run (Gmail auth):**
```bash
uv run zoya-gmail
# Opens browser for OAuth consent
# Saves credentials to ~/.cache/zoya/token.json
```

---

## 📊 Monitoring Commands

```bash
# Real-time dashboard
cat AI_Employee_Vault/Dashboard.md

# Human-readable log
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).log

# Structured JSON log (for parsing)
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json

# Count processed items by type
grep 'type:' AI_Employee_Vault/Done/*.md | cut -d: -f2 | sort | uniq -c

# Count by source channel
grep 'source:' AI_Employee_Vault/Done/*.md | cut -d: -f2 | sort | uniq -c

# Find failed items
ls AI_Employee_Vault/Quarantine/

# Check pending approvals
ls AI_Employee_Vault/Pending_Approval/
```

---

## 🐛 Quick Troubleshooting

| Issue | Command | Solution |
|-------|---------|----------|
| Watcher not running | `ps aux \| grep watcher` | Restart: `Ctrl+C` and `uv run zoya-watcher` |
| Files stuck in In_Progress | `ls AI_Employee_Vault/In_Progress/` | Ralph Wiggum auto-rescues. If stuck >20min, manually move to Needs_Action/ |
| Email not importing | Check credentials | Run: `uv run zoya-gmail` and re-authenticate |
| Dashboard not updating | Check logs | Process a new file to trigger update |
| Social media not posting | Check `.env` | Ensure `*_DRY_RUN=false` and tokens are valid |

---

## 📦 Service Startup Reference

| Service | Command | Port | Purpose |
|---------|---------|------|---------|
| File Watcher | `uv run zoya-watcher` | — | Monitors Inbox/ for new files |
| Orchestrator | `uv run zoya-orchestrator` | — | Processes files in queue |
| Gmail Watcher | `uv run zoya-gmail` | — | Monitors Gmail inbox |
| WhatsApp Watcher | `uv run zoya-whatsapp` | 5001 | Webhook server for WhatsApp |
| Social Media Daemon | `uv run zoya-social-daemon` | — | Posts approved content to LinkedIn/Twitter |
| CEO Briefing | `uv run zoya-briefing` | — | Generates daily/weekly briefings |

**Start all at once:**
```bash
bash scripts/start_gold.sh
```

---

## 📁 Vault Folder Map

| Folder | Purpose | Auto-filled? |
|--------|---------|--------------|
| Inbox/ | Drop files here | Manual |
| Needs_Action/ | Queued files | Watcher |
| In_Progress/ | Currently processing | Orchestrator |
| Done/ | Completed items | Orchestrator |
| Quarantine/ | Failed items | Orchestrator |
| Pending_Approval/ | Needs human review | Orchestrator |
| Approved/ | Ready to publish | Manual |
| Rejected/ | Rejected items | Manual |
| Plans/ | Strategic plans | Orchestrator |
| Briefings/ | Daily/weekly reports | Briefing Generator |
| Business/Tasks/ | Auto-created from WhatsApp | Cross-domain Orchestrator |
| Contacts/ | Unified contact graph | Contact Linker |
| Logs/ | Audit trail | All components |

---

## 🎯 Next Steps

1. ✅ Start system: `bash scripts/start_gold.sh`
2. ✅ Drop a test file: `cp test.pdf AI_Employee_Vault/Inbox/`
3. ✅ Watch processing: `tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).log`
4. ✅ Check dashboard: `cat AI_Employee_Vault/Dashboard.md`
5. ✅ Enable social posting: Set `*_DRY_RUN=false` in `.env`
6. ✅ Deploy: Use systemd services + cron for production

---

## 📚 Full Documentation

- **PROJECT_SUMMARY.md** — Complete system architecture
- **AGENTS.md** — Design rationale and edge cases
- **AI_Employee_Vault/Dashboard.md** — Real-time status
- **AI_Employee_Vault/Logs/** — Complete audit trail

---

**For support:** Check logs and run `uv run zoya-ralph` for system diagnostics.

**For deployment:** Use systemd services and configure cron for daily briefings and maintenance.

---

**Last Updated:** 2026-02-24
**Version:** 0.2.0 (Gold Tier)
**Status:** ✅ Ready to Use
