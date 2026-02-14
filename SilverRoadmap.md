# Silver Tier Roadmap - Zoya

**Prerequisites:** Bronze Tier COMPLETE (all 5/5 requirements passing, 69 tests green)
**Target Time:** 20-30 hours
**Date:** 2026-02-14

---

## Current Roadmap Status

| # | Your Planned Item | Maps to Requirement | Status |
|---|-------------------|---------------------|--------|
| 1 | Gmail Watcher | S2 (Two+ Watchers) | Not started |
| 2 | WhatsApp Watcher | S2 (Two+ Watchers) | Not started |
| 3 | MCP Servers (vault, gmail, calendar) | S5 (One MCP Server) | Not started |
| 4 | HITL Approval Workflow | S6 (HITL Approval) | Not started |
| 5 | Cross-domain Integration | **Not Silver** (Gold tier) | Not started |

---

## Gap Analysis

### MISSING from your roadmap (3 critical gaps)

| # | Official Requirement | Risk Level | Notes |
|---|---------------------|------------|-------|
| S3 | **LinkedIn Auto-Posting** | HIGH | Completely absent. Required: auto-post on LinkedIn for sales. This is a hard Silver requirement. |
| S4 | **Plan.md Reasoning Loop** | MEDIUM | Not mentioned at all. Claude must create Plan.md files for multi-step tasks — structured reasoning, not one-shot. |
| S7 | **Basic Scheduling (cron)** | LOW | Not mentioned. Need at least one cron job or scheduled task (daily briefing, periodic watcher restart, etc.) |

### EXTRA in your roadmap (beyond Silver requirements)

| Item | Actual Tier | Recommendation |
|------|------------|----------------|
| Cross-domain Integration | **Gold** | Remove from Silver scope. You get it naturally when watchers all feed /Inbox/ anyway. Don't waste time formalizing it. |
| Calendar MCP server | **Not required** | Nice-to-have but skip for Silver. One MCP server is enough. |
| vault-mcp server | **Not required** | Claude already reads/writes files via CLI. Low value for Silver. |

### ALREADY COVERED (by Bronze)

| Requirement | Status |
|-------------|--------|
| S1: Bronze requirements | DONE (69 tests, file watcher, orchestrator, dashboard, handbook) |
| S8: Agent Skills architecture | DONE (inbox-processor, dashboard-updater, vault-init already exist) |

---

## Revised Silver Requirements (Prioritized)

| Priority | Requirement | Est. Hours | Complexity | Dependencies |
|----------|-------------|-----------|------------|--------------|
| 1 | S4: Plan.md Reasoning Loop | 2-3h | Low | None — pure skill addition |
| 2 | S6: HITL Approval Workflow | 3-4h | Medium | Needs /Pending_Approval/ folder + orchestrator changes |
| 3 | S7: Basic Scheduling (cron) | 1-2h | Low | Needs a task to schedule |
| 4 | S2a: Gmail Watcher | 4-6h | Medium | Google Cloud project + OAuth2 setup |
| 5 | S5: Email MCP Server | 3-5h | Medium | Gmail credentials (shares setup with S2a) |
| 6 | S2b: WhatsApp Watcher | 4-6h | High | Playwright session or Twilio account |
| 7 | S3: LinkedIn Auto-Posting | 4-6h | High | LinkedIn API or Playwright automation |
| 8 | S8: Agent Skills for all | 2-3h | Low | Write SKILL.md for each new feature |
| | **TOTAL** | **23-35h** | | |

---

## Recommended Implementation Order

```
Phase 1: Quick Wins (3-5 hours)
├── S4: Plan.md Reasoning Loop ────── (new skill, no external deps, instant value)
├── S7: Cron Scheduling ──────────── (simple crontab entry, low effort)
└── S8: Create SKILL.md stubs ─────── (for all planned features)

Phase 2: Core Safety (3-4 hours)
└── S6: HITL Approval Workflow ────── (safety net before external actions)

Phase 3: Gmail Pipeline (7-11 hours)
├── S2a: Gmail Watcher ────────────── (OAuth setup + polling script)
└── S5: Email MCP Server ─────────── (reuse Gmail creds, send capability)

Phase 4: Extra Channels (8-12 hours)
├── S2b: WhatsApp Watcher ─────────── (second watcher requirement)
└── S3: LinkedIn Auto-Posting ─────── (third watcher + posting)
```

### Why this order?

1. **Plan.md first** — Zero external dependencies, makes all later work produce Plan.md files (shows the reasoning loop working). Quick win for demo.
2. **HITL second** — Must be in place before Gmail/MCP can send anything. Safety first.
3. **Cron early** — 30 min to set up a cron job that runs a daily dashboard refresh or inbox check. Easy points.
4. **Gmail third** — Highest-value watcher; reuse credentials for MCP server.
5. **WhatsApp/LinkedIn last** — Riskiest. If time runs out, Gmail + file system = 2 watchers minimum.

---

## Implementation Details

### S4: Plan.md Reasoning Loop (2-3 hours)

**What:** When Claude encounters a multi-step task (invoice processing, complex document), it creates a Plan.md file before executing.

**Implementation:**
- New skill: `.claude/skills/plan-creator/SKILL.md`
- New folder: `AI_Employee_Vault/Plans/`
- Orchestrator modification: for tasks tagged `priority: high` or `type: invoice|contract`, invoke plan-creator skill first, then inbox-processor
- Plan.md format:
  ```markdown
  ---
  created: 2026-02-14T10:00:00Z
  task: FILE_20260214_invoice.md
  status: in_progress
  ---
  ## Objective
  Process invoice from Client A

  ## Steps
  - [x] Read document content
  - [x] Identify document type: invoice
  - [ ] Extract key fields (amount, due date, vendor)
  - [ ] Determine if approval needed (>$500 threshold)
  - [ ] Write summary to metadata file

  ## Approval Required
  No — amount below threshold
  ```

**Risk:** Low. This is a prompt/skill change, not a system change.

### S6: HITL Approval Workflow (3-4 hours)

**What:** Orchestrator routes sensitive items to `/Pending_Approval/` instead of auto-processing.

**Implementation:**
- New folders: `AI_Employee_Vault/Pending_Approval/`, `AI_Employee_Vault/Approved/`, `AI_Employee_Vault/Rejected/`
- New skill: `.claude/skills/hitl-approver/SKILL.md`
- Orchestrator changes:
  1. After Claude processes a file, check if action requires approval
  2. Approval triggers (from Company_Handbook.md):
     - Invoices > $500
     - Contracts with deadlines < 7 days
     - Any outbound email/message
     - File deletions
  3. If approval needed: move to `/Pending_Approval/` with decision prompt
  4. Orchestrator polls `/Approved/` and `/Rejected/` on each cycle
  5. Approved items continue pipeline; rejected items go to `/Done/` with `status: rejected`
- User workflow: open file in Obsidian, change `status: pending` to `status: approved` or `status: rejected`

**Risk:** Medium. Needs orchestrator refactor. Test carefully — don't break existing Bronze flow.

### S7: Basic Scheduling (1-2 hours)

**What:** At least one cron job that triggers the AI employee automatically.

**Options (pick one or more):**
```bash
# Option A: Daily dashboard refresh at 8 AM
0 8 * * * cd /path/to/PIA-CLAUDE && uv run python -m src.orchestrator --once

# Option B: Check inbox every 5 minutes
*/5 * * * * cd /path/to/PIA-CLAUDE && uv run python -m src.orchestrator --once

# Option C: Weekly briefing on Monday 8 AM
0 8 * * 1 cd /path/to/PIA-CLAUDE && claude --print "Generate a weekly briefing using dashboard-updater skill" >> AI_Employee_Vault/Briefings/$(date +\%Y-\%m-\%d).md
```

**Implementation:**
- Add `--once` flag to orchestrator (process queue once, then exit — for cron use)
- Create crontab entries
- New skill: `.claude/skills/scheduled-briefing/SKILL.md` (optional)

**Risk:** Low. Standard Unix tooling.

### S2a: Gmail Watcher (4-6 hours)

**What:** Monitor Gmail for new emails, create action files in `/Inbox/`.

**Setup (takes ~1 hour alone):**
1. Create Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 Desktop credentials
4. Download `credentials.json` to project root
5. First run: browser-based OAuth consent flow -> generates `token.json`
6. Add both to `.gitignore`

**Implementation:**
- File: `src/gmail_watcher.py`
- Skill: `.claude/skills/gmail-processor/SKILL.md`
- Dependencies: `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`
- Flow:
  1. Authenticate via stored token (refresh if expired)
  2. Poll for unread messages (configurable interval, default 120s)
  3. For each new email:
     - Download attachments to `/Inbox/`
     - Create email summary `.md` in `/Inbox/`
     - Mark as read / apply label
  4. Existing watcher pipeline handles the rest

**Risk:** Medium. OAuth setup can be finicky. Token expiry needs handling. Google may require app verification for non-test users.

**Mitigation:** Use "Desktop app" credential type (avoids web app verification). Add yourself as test user in OAuth consent screen.

### S5: Email MCP Server (3-5 hours)

**What:** An MCP server that Claude can use to send emails, search inbox, draft replies.

**Implementation:**
- Directory: `src/mcp/email-server/`
- Config: `.claude/mcp.json`
- Tools exposed:
  - `send_email(to, subject, body, attachments?)` — sends via Gmail API
  - `search_emails(query, max_results?)` — searches inbox
  - `draft_reply(message_id, body)` — creates draft reply
- All send actions MUST go through HITL approval (S6) first

**Risk:** Medium. MCP server protocol requires careful implementation. Consider using `@anthropic/sdk` MCP helpers or existing open-source email MCP servers.

**Alternative:** Use an existing MCP server from `github.com/anthropics/mcp-servers` and configure it, rather than building from scratch.

### S2b: WhatsApp Watcher (4-6 hours)

**What:** Monitor WhatsApp for incoming messages.

**Recommended approach:** Twilio WhatsApp Sandbox (most reliable for hackathon).

| Approach | Effort | Reliability | Cost |
|----------|--------|-------------|------|
| Twilio Sandbox | 2-3h | High | Free trial |
| Playwright (whatsapp-web.js) | 4-6h | Low (breaks often) | Free |
| WhatsApp Business API | 6-10h | High | Requires Meta approval |

**Implementation (Twilio):**
- File: `src/whatsapp_watcher.py`
- Skill: `.claude/skills/whatsapp-processor/SKILL.md`
- Setup: Twilio account + WhatsApp sandbox + ngrok for webhook
- Flow: Twilio webhook -> Flask/FastAPI endpoint -> write .md to `/Inbox/`

**Risk:** HIGH. Twilio requires a publicly accessible webhook (ngrok). Playwright approach is fragile. Budget extra time.

**Mitigation:** If stuck, Gmail + File System = 2 watchers (minimum requirement met). WhatsApp becomes bonus.

### S3: LinkedIn Auto-Posting (4-6 hours)

**What:** Automatically generate and post business content on LinkedIn.

**Approach options:**

| Approach | Effort | Risk |
|----------|--------|------|
| LinkedIn API (OAuth2) | 4-5h | API access requires app review (may take days) |
| Playwright browser automation | 3-4h | Fragile, LinkedIn actively blocks bots |
| Pre-approved MCP (if exists) | 1-2h | Check github.com/anthropics/mcp-servers |

**Implementation:**
- File: `src/linkedin_poster.py`
- Skill: `.claude/skills/linkedin-poster/SKILL.md`
- Flow:
  1. Claude generates post content based on business goals / recent activity
  2. Post goes to `/Pending_Approval/` (HITL — never auto-post without review)
  3. On approval, MCP or Playwright posts to LinkedIn
  4. Log result to `/Done/`

**Risk:** HIGH. LinkedIn API access is the biggest blocker. Apply for API access NOW.

**Fallback plan:** If LinkedIn API is blocked:
1. Generate the post content + save to a file (shows AI generation working)
2. Use Playwright to open LinkedIn and fill the post form (show automation)
3. Require manual "Post" click (HITL) — still demonstrates the flow
4. Document the limitation in your demo

---

## Technical Considerations

### API Limits & Costs
| Service | Free Tier | Rate Limit | Auth Method |
|---------|-----------|------------|-------------|
| Gmail API | 1B quota units/day | 250 units/sec | OAuth2 |
| LinkedIn API | Very limited | 100 calls/day (varies) | OAuth2 |
| Twilio WhatsApp | Free sandbox | Limited messages | API key |
| Claude Code | Pro subscription | Per-model limits | API key |

### Authentication Matrix
| Service | Token Type | Expiry | Refresh Strategy |
|---------|-----------|--------|-----------------|
| Gmail | OAuth2 access + refresh token | 1 hour (access) | Auto-refresh via google-auth library |
| LinkedIn | OAuth2 access token | 60 days | Manual re-auth needed |
| Twilio | API Key + Auth Token | Never (until rotated) | Store in .env |

### Security Checklist
- [ ] `.env` in `.gitignore` (verify)
- [ ] `credentials.json` in `.gitignore`
- [ ] `token.json` in `.gitignore`
- [ ] No hardcoded secrets in source code
- [ ] HITL required for all outbound actions (email, LinkedIn, WhatsApp)
- [ ] Dry-run mode for development (`DRY_RUN=true` in .env)
- [ ] Audit logging for all external actions

### Process Management
For Silver, you'll have 3-4 concurrent processes:
```
Terminal 1: uv run python -m src.watcher          # File system watcher
Terminal 2: uv run python -m src.gmail_watcher     # Gmail watcher
Terminal 3: uv run python -m src.orchestrator      # Orchestrator (processes all)
Terminal 4: uv run python -m src.whatsapp_watcher  # WhatsApp (optional)
```

Consider using PM2 or a simple shell script to manage all:
```bash
#!/bin/bash
# start_silver.sh
uv run python -m src.watcher &
uv run python -m src.gmail_watcher &
uv run python -m src.orchestrator &
echo "Silver tier running. Press Ctrl+C to stop all."
wait
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LinkedIn API access denied/delayed | High | High (S3 blocker) | Apply NOW. Fallback: Playwright + manual post |
| WhatsApp Playwright breaks | Medium | Medium | Fallback: Twilio sandbox |
| Gmail OAuth consent screen rejected | Low | High | Use "Testing" mode, add self as test user |
| MCP server protocol errors | Medium | Medium | Use existing MCP server templates |
| Token expiry during demo | Medium | High | Test refresh flow; re-auth before demo |
| Time runs out before all 8 items | Medium | High | Prioritize: Plan.md + HITL + Gmail + cron = 4 quick items |

---

## Next Immediate Steps

1. **Right now:** Apply for LinkedIn API access (it takes time for approval — do this first)
2. **Today (1-2h):** Implement S4 — Plan.md reasoning loop skill. Zero external deps, pure skill file + minor orchestrator change. Instant demo value.
3. **Today (30 min):** Set up cron job (S7) — add `--once` flag to orchestrator, create crontab entry for daily dashboard refresh.
4. **Tomorrow (3-4h):** Build HITL approval workflow (S6) — new folders, orchestrator changes, approval polling.
5. **Next (4-6h):** Gmail Watcher + Email MCP (S2a + S5) — set up Google Cloud project, OAuth, watcher script, MCP server.

---

## Minimum Viable Silver (if time is short)

If you only have 15 hours, focus on these 6 items to pass Silver:

| Item | Hours | Why |
|------|-------|-----|
| S4: Plan.md loop | 2h | Easy skill, big demo impact |
| S6: HITL workflow | 4h | Required, shows safety |
| S7: Cron scheduling | 1h | Quick win |
| S2a: Gmail Watcher | 5h | Primary second watcher |
| S5: Email MCP | 3h | Reuses Gmail setup |
| S3: LinkedIn (dry-run) | 2h | Generate content + show flow, even without live posting |
| **Total** | **17h** | |

This skips WhatsApp (Gmail + File System = 2 watchers) and uses dry-run LinkedIn posting as a fallback. Not ideal but passes the requirements.
