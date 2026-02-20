# Zoya — Permissions & Autonomy Model

_Last updated: 2026-02-20_

This document defines exactly what each Zoya component can do **autonomously**
vs what **requires explicit human approval** before execution.

---

## Guiding Principles

1. **No irreversible action without approval** — sending emails, posting to social
   media, or initiating payments always go through HITL first.
2. **Read freely, write carefully** — reading vault files is always autonomous;
   writing to external systems requires approval.
3. **Payment actions are sacred** — `NEVER auto-retry`. Every payment attempt
   requires a fresh, explicit human approval file move.
4. **Dry-run default** — all external-send integrations default to `DRY_RUN=true`.
   Live publishing requires explicit `.env` opt-in.

---

## Component Permissions

### 1. File System Watcher (`src/watcher.py`)

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Read files from `/Inbox/` | ✅ Yes | Core function |
| Write metadata `.md` to `/Needs_Action/` | ✅ Yes | Creates job queue entry |
| Move file to `/Quarantine/` | ✅ Yes | Unsupported type / too large |
| Delete duplicate files from `/Inbox/` | ✅ Yes | Dedup by SHA-256 hash |
| Send anything externally | ❌ Never | Watcher is read-only |

---

### 2. Orchestrator (`src/orchestrator.py`)

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Move files: Needs_Action → In_Progress | ✅ Yes | Claim-by-move |
| Move files: In_Progress → Done | ✅ Yes | After successful processing |
| Move files: In_Progress → Quarantine | ✅ Yes | After MAX_RETRIES failures |
| Move files: Pending_Approval → Done | ✅ Yes | Only after human puts in Approved/ |
| Invoke Claude/Qwen/Ollama | ✅ Yes | Core processing |
| Update Dashboard.md | ✅ Yes | Read-only aggregation |
| Create Plan.md | ✅ Yes | Analysis document only |
| Send emails | ❌ Never | Must go through HITL approval |
| Post to social media | ❌ Never | Must go through HITL approval |
| Initiate payments | ❌ Never | Requires explicit human approval |

---

### 3. Gmail Watcher (`src/watchers/gmail_watcher.py`)

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Read inbox | ✅ Yes | OAuth read-only scope sufficient |
| Create metadata files in `/Needs_Action/` | ✅ Yes | Queue entries only |
| **Send emails** | ❌ Approval required | Creates `SEND_EMAIL_*.md` in Pending_Approval/ |
| Delete emails | ❌ Never | Zoya never deletes emails |

---

### 4. Email MCP Server (`src/mcp/email_server.py`)

| Tool | Autonomous? | Notes |
|------|------------|-------|
| `list_recent_emails` | ✅ Yes | Read-only |
| `search_emails` | ✅ Yes | Read-only |
| `send_email` | ❌ Approval required | Creates approval file; human must move to Approved/ |

---

### 5. WhatsApp Watcher (`src/watchers/whatsapp_watcher.py`)

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Receive messages | ✅ Yes | Webhook listener |
| Create metadata in `/Needs_Action/` | ✅ Yes | Queue entry |
| **Reply to messages** | ❌ Approval required | Creates approval file |
| **Send unprompted messages** | ❌ Never | Only replies, only with approval |

---

### 6. Twitter MCP Server (`src/mcp_servers/twitter_mcp.py`)

| Tool | Autonomous? | Notes |
|------|------------|-------|
| `get_timeline` | ✅ Yes | Read-only |
| `get_tweet_metrics` | ✅ Yes | Read-only |
| `read_content_calendar` | ✅ Yes | Read-only |
| `draft_tweet` | ❌ Approval required | Creates TWITTER_*.md in Pending_Approval/ |
| `schedule_tweet` | ❌ Approval required | Creates TWITTER_*.md in Pending_Approval/ |
| `process_approved_tweets` | ✅ Yes (if TWITTER_DRY_RUN=false) | Only processes files in Approved/ — human put them there |

---

### 7. LinkedIn Poster (`src/linkedin_poster.py`)

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Generate post draft | ✅ Yes | Creates LINKEDIN_*.md in Pending_Approval/ |
| **Publish post** | ❌ Approval required | Only after human moves to Approved/ |

---

### 8. Audit Logger (`src/audit_logger.py`)

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Write log entries | ✅ Yes | Append-only to YYYY-MM-DD.json |
| Read log entries | ✅ Yes | For briefings and summaries |
| Purge logs >90 days | ✅ Yes | Retention policy |
| Append weekly summary to Dashboard.md | ✅ Yes | Read-only aggregation |

---

### 9. Briefing Generator / Audit Generator

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Read vault folders | ✅ Yes | Aggregation only |
| Write briefing to `/Vault/Briefings/` | ✅ Yes | New file, not modifying existing |
| **Send WhatsApp summary** | ✅ Yes | Informational only; no action triggered |
| **Send briefing via email** | ❌ Approval required | If implemented, goes through HITL |

---

### 10. Error Recovery (`src/error_recovery.py`)

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Retry transient/rate-limit errors | ✅ Yes | Up to configured max_attempts |
| Create auth error alert in Needs_Action/ | ✅ Yes | Alert only; human must fix credentials |
| Create payment error alert in Pending_Approval/ | ✅ Yes | Alert only; human must re-approve |
| **Retry payment actions** | ❌ Never | Fresh approval always required |
| Queue items to /Vault/Queue/ offline | ✅ Yes | Preserves work, never discards |

---

### 11. Ralph Wiggum (`src/ralph_wiggum.py`)

| Action | Autonomous? | Notes |
|--------|------------|-------|
| Re-invoke Claude for stuck tasks | ✅ Yes | Up to max_iterations |
| Create RALPH_EXHAUSTED alert | ✅ Yes | Alert only |
| **Approve/reject any HITL item** | ❌ Never | Ralph never moves files to Approved/ |
| **Initiate payments** | ❌ Never | Payment actions blocked entirely |

---

## Approval Thresholds Summary

| Threshold | Value | Applies To |
|-----------|-------|------------|
| Invoice amount requiring approval | > $500 | Invoices |
| Email requiring approval | All outbound | Gmail sends |
| Social post requiring approval | All posts | Twitter, LinkedIn, Meta |
| Payment requiring approval | All payments | Odoo, bank |
| Days overdue before alert | 30 days | Outstanding invoices |
| Unusual transaction alert | > $1,000 | Bank transactions |

---

## DRY_RUN Defaults (`.env`)

```
TWITTER_DRY_RUN=true        # Set to false to enable live Twitter posting
LINKEDIN_DRY_RUN=true       # Set to false to enable live LinkedIn posting
GMAIL_DRY_RUN=true          # Not yet implemented; placeholder
WHATSAPP_DRY_RUN=true       # Set to false to enable live WhatsApp sends
ODOO_DRY_RUN=true           # Set to false to enable live Odoo writes
```

_All integrations default to DRY_RUN=true. Never set to false in production
without verifying the full HITL approval chain is working correctly._
