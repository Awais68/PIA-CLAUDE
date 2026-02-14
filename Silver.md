# Silver Tier Roadmap - Zoya

**Prerequisites:** Bronze Tier COMPLETE (all 5/5 requirements passing, 69 tests green)

---

## Silver Requirements

| # | Requirement | Status | Priority |
|---|-------------|--------|----------|
| 1 | Gmail Watcher | Not started | High (start here) |
| 2 | WhatsApp Watcher | Not started | Medium |
| 3 | MCP Servers | Not started | Medium |
| 4 | HITL Approval Workflow | Not started | High |
| 5 | Cross-domain Integration | Not started | Low (depends on 1-4) |

---

## 1. Gmail Watcher

**Goal:** Monitor a Gmail inbox for new emails, extract attachments, and drop them into `/Inbox/` for the existing pipeline.

### Setup

1. Create a Google Cloud project at https://console.cloud.google.com
2. Enable the Gmail API
3. Create OAuth 2.0 credentials (Desktop app) and download `credentials.json`
4. Add credentials to `.gitignore` (never commit secrets)

### Dependencies

```toml
# Add to pyproject.toml [project.dependencies]
"google-api-python-client>=2.0.0",
"google-auth-oauthlib>=1.0.0",
"google-auth-httplib2>=0.2.0",
```

### Implementation

- **File:** `src/gmail_watcher.py`
- **Skill:** `.claude/skills/gmail-processor/SKILL.md`
- **Flow:**
  1. Authenticate via OAuth (first run opens browser for consent)
  2. Poll Gmail API for unread messages (configurable interval)
  3. For each new email:
     - Download attachments to `AI_Employee_Vault/Inbox/`
     - Create a `.md` summary of the email body in `/Inbox/`
     - Mark email as read (or apply a label)
  4. Existing watcher + orchestrator pipeline handles the rest

### Config Additions

```python
# src/config.py
GMAIL_POLL_INTERVAL = 30  # seconds
GMAIL_LABEL = "INBOX"
GMAIL_CREDENTIALS = PROJECT_ROOT / "credentials.json"
GMAIL_TOKEN = PROJECT_ROOT / "token.json"
```

### Entry Point

```toml
# pyproject.toml [project.scripts]
zoya-gmail = "src.gmail_watcher:main"
```

---

## 2. WhatsApp Watcher

**Goal:** Monitor WhatsApp for incoming messages and route them into the vault pipeline.

### Options

| Approach | Pros | Cons |
|----------|------|------|
| Twilio WhatsApp API | Official, reliable, good docs | Paid, requires Twilio account |
| WhatsApp Business API | Direct integration | Complex setup, Meta approval needed |
| whatsapp-web.js (bridge) | Free, no approval needed | Unofficial, may break |

### Implementation

- **File:** `src/whatsapp_watcher.py`
- **Skill:** `.claude/skills/whatsapp-processor/SKILL.md`
- **Flow:**
  1. Listen for incoming messages via webhook (Twilio) or polling
  2. Extract text content and media attachments
  3. Write message content as `.md` to `/Inbox/`
  4. Download media attachments to `/Inbox/`
  5. Existing pipeline processes them

---

## 3. MCP Servers

**Goal:** Add Model Context Protocol servers so Claude can use structured tools instead of raw CLI prompts.

### Planned MCP Servers

| Server | Purpose |
|--------|---------|
| `vault-mcp` | Read/write/list vault files with proper tool schemas |
| `gmail-mcp` | Search, read, send emails via structured tool calls |
| `calendar-mcp` | Read/create calendar events |

### Implementation

- **Directory:** `src/mcp/`
- **Config:** `.claude/mcp.json`
- Each server exposes tools via the MCP protocol that Claude can call directly
- Replaces the current `--print` CLI approach with structured tool use

---

## 4. HITL (Human-in-the-Loop) Approval Workflow

**Goal:** Require human approval before executing high-stakes actions.

### Approval Triggers

| Action | Requires Approval |
|--------|-------------------|
| Processing invoices > $500 | Yes |
| Contracts with deadlines < 7 days | Yes |
| Sending emails on user's behalf | Yes |
| Deleting or archiving files | Yes |
| Low-priority notes | No (auto-process) |

### Implementation

- **New folder:** `AI_Employee_Vault/Pending_Approval/`
- **Flow:**
  1. Orchestrator identifies items needing approval (based on Company_Handbook rules)
  2. Moves item to `/Pending_Approval/` with a decision prompt in the metadata
  3. User reviews in Obsidian and marks `approved: true` or `rejected: true`
  4. Orchestrator picks up approved items and continues processing
  5. Rejected items move to `/Done/` with status `rejected`

### Notification Options

- Obsidian notification plugin
- Desktop notification via `notify-send` (Linux) / `osascript` (macOS)
- Telegram bot message
- Email notification

---

## 5. Cross-domain Integration

**Goal:** Unify all watchers (file system, Gmail, WhatsApp) into a single pipeline with shared context.

### Architecture

```
Gmail ──────┐
             │
File System ─┼──> /Inbox/ ──> Watcher ──> /Needs_Action/ ──> Orchestrator ──> Claude
             │
WhatsApp ───┘
```

- All sources funnel into the same `/Inbox/` folder
- Metadata files include a `source` field: `file_drop`, `gmail`, `whatsapp`
- Dashboard shows activity breakdown by source
- Company_Handbook rules can be source-specific

---

## Recommended Implementation Order

```
1. Gmail Watcher ──────────────── (reuses existing pipeline, highest value)
2. HITL Approval Workflow ─────── (safety before adding more inputs)
3. MCP Servers ────────────────── (better Claude integration)
4. WhatsApp Watcher ───────────── (new input channel)
5. Cross-domain Integration ───── (ties everything together)
```

---

## Running Silver (Target State)

```bash
# Terminal 1: File System Watcher
uv run python -m src.watcher

# Terminal 2: Gmail Watcher
uv run python -m src.gmail_watcher

# Terminal 3: Orchestrator (processes all sources)
uv run python -m src.orchestrator

# Terminal 4 (optional): WhatsApp Watcher
uv run python -m src.whatsapp_watcher
```
