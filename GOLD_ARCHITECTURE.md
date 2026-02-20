# Zoya Gold Tier — Complete Architecture

**Status:** Gold Tier  
**Last Updated:** 2026-02-20  
**Stack:** Claude Code · Python (uv) · Obsidian Vault · FastMCP · Tweepy · Requests

---

## 1. System Overview

Zoya is a Personal AI Employee that operates autonomously on a local-first,
file-driven architecture. All state lives in `AI_Employee_Vault/` as Markdown
files — Obsidian is the GUI, the file system is the database.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ZOYA GOLD TIER                              │
│                                                                 │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐ │
│  │ Gmail   │  │ WhatsApp │  │ File Drop  │  │  Scheduler   │ │
│  │ Watcher │  │ Watcher  │  │  (Inbox/)  │  │ (cron/jobs)  │ │
│  └────┬────┘  └────┬─────┘  └─────┬──────┘  └──────┬───────┘ │
│       │            │              │                  │         │
│       └────────────┴──────────────┴──────────────────┘         │
│                              │                                  │
│                        Needs_Action/                            │
│                              │                                  │
│                    ┌─────────▼──────────┐                      │
│                    │    Orchestrator     │                      │
│                    │  (claim-by-move)   │                      │
│                    └─────────┬──────────┘                      │
│                              │                                  │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐           │
│        │   Claude  │  │   Qwen    │  │   Ollama  │           │
│        │ (primary) │  │(DashScope)│  │  (local)  │           │
│        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘           │
│              └───────────────┼───────────────┘                  │
│                              │                                  │
│                    ┌─────────▼──────────┐                      │
│                    │  HITL Evaluator    │                      │
│                    │ (approval router)  │                      │
│                    └─────────┬──────────┘                      │
│                              │                                  │
│              ┌───────────────┼───────────────┐                  │
│              │               │               │                  │
│         Pending_         Approved/       Done/                  │
│         Approval/        (human OK)    (archive)                │
│              │                                                  │
│              │  Human reviews in Obsidian                       │
│              └─────────────────────────────────────────────────│
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. All Integrations & Data Flows

### 2.1 File System Watcher (Bronze)
**Flow:** File dropped in Inbox/ → watcher detects → validates (size, type, hash) →
creates `FILE_*.md` metadata in Needs_Action/ → orchestrator picks up

### 2.2 Gmail Integration (Silver)
**Flow:** Gmail API poll (every 60s) → new emails → `FILE_EMAIL_*.md` in Needs_Action/ →
orchestrator processes with `gmail-processor` skill → HITL if high-priority →
contact linked in Contacts/

### 2.3 WhatsApp Business (Silver)
**Flow:** Webhook POST from Meta → Flask handler → `FILE_WA_*.md` in Needs_Action/ →
orchestrator processes → action items extracted → reply goes through HITL

### 2.4 LinkedIn Auto-Poster (Silver)
**Flow:** Content generated → `LINKEDIN_*.md` in Pending_Approval/ → human approves →
moves to Approved/ → orchestrator publishes via LinkedIn UGC API

### 2.5 Twitter/X (Gold)
**Flow (post):** `draft_tweet` tool creates `TWITTER_*.md` in Pending_Approval/ →
human moves to Approved/ → `process_approved_tweets` publishes via tweepy v2

**Flow (schedule):** `schedule_tweet` stamps `scheduled_for` → sits in Pending_Approval/
until human approves before scheduled time

**Flow (metrics):** `get_tweet_metrics(tweet_id)` fetches live from API v2

**Flow (calendar):** `read_content_calendar` scans `Business/Content_Calendar.md`

### 2.6 Email MCP Server (Silver S5)
**Tools:** `send_email` (HITL) · `search_emails` · `list_recent_emails`  
**Transport:** stdio (registered in `.claude/mcp.json`)

### 2.7 Twitter MCP Server (Gold)
**Tools:** `draft_tweet` · `schedule_tweet` · `get_timeline` · `get_tweet_metrics` ·
`process_approved_tweets` · `read_content_calendar`  
**Transport:** stdio

### 2.8 CEO Briefing / Audit Generator (Gold)
**Schedule:** Sunday 23:00 via cron  
**Flow:** collect_vault_snapshot() + collect_social_metrics() + collect_financial_summary()
→ generate_ceo_briefing() → save to Briefings/ → send_whatsapp_summary() → purge_old_logs()

### 2.9 Error Recovery (Gold)
**Used by:** all external API callers  
**Strategies:** exponential backoff → auth alert → payment HITL → offline queue

### 2.10 Audit Logger (Gold)
**Written by:** every module that performs an action  
**Read by:** briefing generator, dashboard updater, weekly summary

### 2.11 Ralph Wiggum Loop (Gold)
**Triggered by:** orchestrator (stuck In_Progress > 20 min) or manual  
**Flow:** Claude call → check promise/glob → re-inject if needed → exhausted alert

### 2.12 Cross-Domain Contact Linker (Gold G3)
**Flow:** After each Done/ item → extract email/phone → create/update
`CONTACT_<key>.md` in Contacts/ with interaction history

### 2.13 Ralph Loop (G2 self-monitoring, separate from Wiggum)
**Checks:** stuck In_Progress · high quarantine · approval backlog · stale pending  
**Output:** `RALPH_*.md` alerts in Pending_Approval/

---

## 3. Security Model

### 3.1 Credential Management
- **All secrets** in `.env` only — never hardcoded, never committed
- `.gitignore` excludes: `.env`, `credentials.json`, `token.json`, `*.key`
- `.env.example` documents every variable with placeholder values

### 3.2 Per-Integration Security

| Integration | Auth Method | Scope | DRY_RUN Default |
|-------------|------------|-------|----------------|
| Gmail | OAuth 2.0 + token.json | read + send | N/A |
| WhatsApp | Bearer token (Meta) | send messages | true |
| Twitter | OAuth 1.0a (4-token) | read/write | true |
| LinkedIn | OAuth 2.0 Bearer | read/write | true |
| Odoo | API key (header) | full ERP | true |
| Meta/Instagram | Long-lived Page token | publish | true |

### 3.3 HITL Security Gates
Every outbound action (email, post, payment) creates an approval file.
The human moves it to `/Approved/` — this is the only way external actions fire.
No code path bypasses this for payment or social publishing actions.

### 3.4 Rate Limiting
Each integration respects configurable RPM limits via `.env`:
`TWITTER_RATE_LIMIT_RPM=15`, `META_RATE_LIMIT_RPM=60`, etc.

---

## 4. Vault Folder Structure (Gold)

```
AI_Employee_Vault/
├── Dashboard.md                    # Real-time status + weekly audit summary
├── Company_Handbook.md             # Business rules for Zoya
├── Permissions.md                  # What Zoya can do autonomously vs approval
│
├── Inbox/                          # Drop zone — monitored by watcher
├── Needs_Action/                   # Queue — ALERT_*.md + FILE_*.md
├── In_Progress/                    # Claimed — one at a time
├── Done/                           # Archive — all completed items
├── Quarantine/                     # Failed after max retries
├── Pending_Approval/               # Waiting for human: TWITTER_*, SEND_EMAIL_*
├── Approved/                       # Human-approved — ready to execute
├── Rejected/                       # Human-rejected — archived to Done/
├── Plans/                          # PLAN_*.md reasoning docs for complex items
│
├── Briefings/                      # CEO_BRIEFING_*.md + BRIEFING_*.md
├── Contacts/                       # CONTACT_<key>.md cross-channel profiles
├── Logs/                           # YYYY-MM-DD.{log,json} + gold_tier_progress.md
├── Queue/                          # Offline queue: Queue/<component>/QUEUED_*.json
│   ├── twitter/
│   ├── gmail/
│   ├── odoo/
│   └── ...
├── Business/                       # Company_Handbook, Content_Calendar, Odoo snapshots
│   ├── Content_Calendar.md
│   └── odoo_snapshot.json          # Written by Odoo MCP (when connected)
├── Clients/                        # Client-specific folders
│
└── .ralph_state/                   # Ralph Wiggum loop state files (hidden)
    └── task_<TIMESTAMP>.json
```

---

## 5. Agent Skills Reference

| Skill | File | Trigger | Key Outputs |
|-------|------|---------|-------------|
| inbox-processor | `.claude/skills/inbox-processor/SKILL.md` | Orchestrator | metadata file updated |
| dashboard-updater | `.claude/skills/dashboard-updater/SKILL.md` | After each batch | Dashboard.md |
| gmail-processor | `.claude/skills/gmail-processor/SKILL.md` | Email files | metadata + contact |
| whatsapp-processor | `.claude/skills/whatsapp-processor/SKILL.md` | WA files | metadata + reply draft |
| contact-linker | `.claude/skills/contact-linker/SKILL.md` | After Done/ | Contacts/CONTACT_*.md |
| plan-creator | `.claude/skills/plan-creator/SKILL.md` | Invoice/contract | Plans/PLAN_*.md |
| hitl-evaluator | `.claude/skills/hitl-evaluator/SKILL.md` | After processing | routes to Pending_Approval/ |
| linkedin-poster | `.claude/skills/linkedin-poster/SKILL.md` | Content calendar | LINKEDIN_*.md |
| content-generator | `.claude/skills/content-generator/SKILL.md` | Manual/scheduled | draft posts |
| email-triage | `.claude/skills/email_triage/SKILL.md` | Gmail batch | prioritised queue |
| scheduled-briefing | `.claude/skills/scheduled-briefing/SKILL.md` | Daily/weekly | BRIEFING_*.md |
| ralph-monitor | `.claude/skills/ralph-monitor/SKILL.md` | Every orchestrator cycle | RALPH_*.md alerts |
| ralph-wiggum | `.claude/skills/ralph-wiggum/SKILL.md` | Stuck tasks | re-invokes Claude |
| error-recovery | `.claude/skills/error-recovery/SKILL.md` | API failures | retry / alert / queue |
| audit-logger | `.claude/skills/audit-logger/SKILL.md` | All actions | YYYY-MM-DD.json |
| ceo-briefing | `.claude/skills/ceo-briefing/SKILL.md` | Sunday 11 PM | CEO_BRIEFING_*.md + WhatsApp |

---

## 6. Running the Gold Tier

### Start all services

```bash
# Terminal 1: File system watcher
uv run zoya-watcher

# Terminal 2: Orchestrator (includes Ralph Wiggum + cross-domain)
uv run zoya-orchestrator

# Terminal 3: Gmail watcher
uv run zoya-gmail

# Terminal 4: WhatsApp webhook listener
uv run zoya-whatsapp

# MCP servers (registered in .claude/mcp.json — auto-started by Claude Code)
# zoya-email, zoya-twitter, zoya-odoo, zoya-meta, zoya-whatsapp
```

### Cron jobs

```bash
# Sunday 11 PM — CEO briefing + audit
0 23 * * 0 cd /path/to/project && uv run zoya-audit

# Daily 7 AM — daily briefing
0 7 * * * cd /path/to/project && uv run zoya-briefing
```

### One-off commands

```bash
uv run zoya-briefing --weekly          # generate weekly briefing now
uv run zoya-audit --force              # run Sunday audit any day
uv run zoya-audit --dry-run --force    # test without WhatsApp/APIs
uv run python -m src.ralph_wiggum \    # run Ralph loop manually
    --prompt "..." --promise "done" --dry-run
```

---

## 7. Known Limitations & Future Improvements

### Current Limitations

1. **Financial data** — `collect_financial_summary()` returns placeholders until Odoo MCP is wired with live credentials and `odoo_snapshot.json` cache is populated.

2. **Social metrics** — Twitter impressions, Facebook reach, Instagram follower delta require live API credentials (`TWITTER_DRY_RUN=false`, `META_DRY_RUN=false`). Until then, counts come from audit logs only.

3. **WhatsApp briefing delivery** — Requires `OWNER_WHATSAPP_NUMBER` in `.env` and a verified WhatsApp Business account.

4. **Ralph Wiggum re-injection context** — Limited to last 2,000 chars of previous Claude output. Very long documents may lose context. Future: summarise previous output before re-injection.

5. **Offline queue replay** — Items queued in `/Vault/Queue/` are not automatically replayed when a component recovers. Caller must invoke `flush_offline_queue()` on health check. Future: add to orchestrator cycle.

6. **Concurrent watcher instances** — Only the orchestrator has a PID lock. Running two Gmail watchers simultaneously will create duplicate Needs_Action entries.

### Planned Improvements

- Platinum tier: cloud deployment (Railway/Fly.io) + always-on operation
- Stripe integration for payment reconciliation
- Google Calendar integration for deadline extraction
- Multi-user support (separate vaults per team member)
- Automated test suite for all skills via pytest + vault fixture

---

## 8. Setup Checklist for New Installations

```
[ ] Copy .env.example to .env and fill in credentials
[ ] Run: uv sync
[ ] Run: claude "Initialize the Zoya vault using the vault-init skill"
[ ] Set up Gmail OAuth: uv run python scripts/setup_gmail_auth.py
[ ] Set up WhatsApp webhook (ngrok for dev, public URL for prod)
[ ] Add Twitter API keys to .env
[ ] Add LinkedIn token to .env
[ ] Set OWNER_WHATSAPP_NUMBER in .env
[ ] Test with dry-run: uv run zoya-audit --dry-run --force
[ ] Disable dry-run for each service you're ready to go live with
[ ] Add Sunday 11 PM cron: 0 23 * * 0 uv run zoya-audit
[ ] Add daily 7 AM briefing cron: 0 7 * * * uv run zoya-briefing
```
