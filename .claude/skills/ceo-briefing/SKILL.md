---
skill_name: CEOBriefing
version: 2.0
trigger: "Sunday 11 PM via cron (audit_generator.py) OR manual: uv run zoya-audit --force"
inputs:
  - AI_Employee_Vault/Done/                          # completed tasks (last 7 days)
  - AI_Employee_Vault/Needs_Action/                  # still pending items
  - AI_Employee_Vault/Logs/YYYY-MM-DD.json           # audit logs last 7 days
  - AI_Employee_Vault/Business_Goals.md              # revenue targets + key metrics
  - AI_Employee_Vault/Logs/gold_tier_progress.md     # prior week briefing for WoW comparison
  - AI_Employee_Vault/Briefings/CEO_BRIEFING_*.md    # most recent briefing for WoW diff
  - AI_Employee_Vault/Quarantine/                    # failed/error items
outputs:
  - AI_Employee_Vault/Briefings/CEO_BRIEFING_YYYYMMDD_HHMMSS.md  # timestamped (no overwrite)
  - AI_Employee_Vault/Briefings/CEO_BRIEFING_LATEST.md            # always overwritten with latest
  - AI_Employee_Vault/Dashboard.md                                 # "Last CEO Briefing" line updated
  - WhatsApp message to OWNER_WHATSAPP_NUMBER (or Pending_Approval/ on failure)
  - AI_Employee_Vault/Logs/gold_tier_progress.md                  # execution time + status appended
approval_required: "no — read-only aggregation; WhatsApp is best-effort with fallback"
max_runtime: 10
---

## Objective

Generate the Monday Morning CEO Briefing with all 7 required sections,
aggregating data from vault folders, audit logs, social metrics, and financials.
The briefing answers: *How much did we earn? What got done? What's blocked?*

---

## Step-by-Step Process

### Step 1 — Collect vault snapshot
- Count files in each folder: `Done/`, `Needs_Action/`, `In_Progress/`, `Quarantine/`, `Pending_Approval/`
- Filter Done/ to last 7 days using `processed_at` frontmatter
- Identify overdue items: `Needs_Action/` files older than 48h

### Step 2 — Collect social metrics
- Twitter: count posts, reads, and mentions from `Logs/YYYY-MM-DD.json` (`action_type: twitter_post`)
- LinkedIn: count posts from audit log (`action_type: linkedin_post`)
- API metric snapshots from watcher output files if available in `Done/`

### Step 3 — Collect financial data
Read from these sources in order of preference:
1. **Odoo** (if `ODOO_DB` set): call `odoo_list_invoices(state="posted")` via MCP
2. **Bank transactions**: scan `Done/` for `type: bank_transaction` items in period
3. **Business_Goals.md**: read monthly revenue target and current MTD

If Odoo is unavailable, use exactly this placeholder:
> ⚠️ Financial data unavailable (Odoo offline).
> Manual review required. Check previous briefing for last known figures.
> Action: Start Odoo with `docker compose up odoo` then re-run with `--force`

### Step 4 — Get audit stats
```python
from src.audit_logger import get_period_stats
stats = get_period_stats(days=7)
# returns: {total_actions, by_type, errors, approvals, rejections}
```

### Step 5 — Load previous briefing for week-over-week comparison
- Find most recent `CEO_BRIEFING_*.md` in `Briefings/` (excluding the one being generated)
- Extract: `revenue_period`, `tasks_completed`, `items_quarantined`
- If no previous briefing exists: WoW columns show "N/A (first run)"

### Step 6 — Generate CEO briefing with EXACT sections

All 7 sections must be present, in this order:

```markdown
## Financial Summary
- Revenue This Week: $X  (vs $Y last week = +/-Z%)
- MTD Revenue: $A / $B goal (C%)
- Paid Invoices: N
- Unpaid/Overdue Invoices: M  ← flag if any overdue > 30 days
- Largest transaction: $X — PayeeName (DEBIT/CREDIT)
[Odoo unavailable placeholder if applicable]

## Completed This Week
- Tasks completed: N  (vs M last week = +/-Z%)
- By channel: Gmail: A | WhatsApp: B | File Drop: C
- By type: invoice: X | contract: Y | email: Z | other: W
[Table of top 10 completed items: name | type | priority | date]

## Bottlenecks
- Items in Quarantine: N  (flag if > 3)
- Items stuck in Needs_Action > 48h: N
- Items awaiting approval > 24h: N
- Ralph alerts created this week: N
[List each bottleneck item with age and reason]

## Social Media Performance
- Tweets posted: N | LinkedIn posts: N | Facebook posts: N
- Mentions/interactions (if watcher data available): N
- Pending drafts in approval queue: N

## Alerts Requiring Attention
- [List any RALPH_*.md or ALERT_*.md files in Needs_Action/]
- [List items in Quarantine with reason]
- [Payment errors in Pending_Approval/]
- If no alerts: "✅ No alerts — all systems operational"

## Proactive Suggestions
- [Subscriptions with no activity in 30+ days — from bank transactions matching SUBSCRIPTION_PATTERNS]
- [Clients with unpaid invoices > BRIEFING_ALERT_INVOICE_OVERDUE_DAYS]
- [Transactions > BRIEFING_ALERT_TRANSACTION_THRESHOLD needing review]
- [System health score < 80: recommend running: uv run zoya-ralph]

## Week Ahead
- Items currently in Needs_Action (unprocessed): N
- Scheduled jobs for next week (from crontab.example)
- Upcoming deadlines extracted from recent Done/ action items
- Recommended action if health_score < 80
```

### Step 7 — Validate before saving

**Run these checks before writing any file:**

- Every section header (`## X`) must have at least 1 non-empty content line beneath it
- `## Financial Summary` must contain at least one numeric value (revenue, invoice count, or balance)
- `## Completed This Week` must contain a task count (even if 0)
- All 7 section headers must be present

**If validation fails:**
- Save as `CEO_BRIEFING_DRAFT_YYYYMMDD_HHMMSS.md` (not the final name)
- Create `AI_Employee_Vault/Needs_Action/ALERT_briefing_incomplete_YYYYMMDD.md`
- Do NOT overwrite `CEO_BRIEFING_LATEST.md`
- Do NOT send WhatsApp
- Log `result: briefing_draft` (not `briefing_complete`)

**If validation passes:**
- Save as `CEO_BRIEFING_YYYYMMDD_HHMMSS.md` (with full timestamp — never overwrites previous)
- Copy/overwrite `CEO_BRIEFING_LATEST.md` with same content
- Proceed to Steps 8–10

### Step 8 — Update Dashboard.md
After successful save, update this line in `Dashboard.md`:
```
**Last CEO Briefing:** [YYYY-MM-DD](Briefings/CEO_BRIEFING_YYYYMMDD_HHMMSS.md) ✅
```
Use regex replace on the existing line; add it if not present.

### Step 9 — Send WhatsApp summary to owner

**7a.** Build a short summary (max 500 chars):
```
📊 Zoya Weekly Briefing — YYYY-MM-DD
Revenue: $X this week (MTD: $Y / $Z goal)
✅ N tasks done | ⚠️ M quarantined | 🕐 P pending approval
[Top 1–2 alerts if any]
Full briefing: Briefings/CEO_BRIEFING_YYYYMMDD_HHMMSS.md
```

**7b.** Attempt send via `whatsapp_mcp.py` using `WHATSAPP_SESSION_PATH`
- Timeout: `WHATSAPP_SEND_TIMEOUT_SECONDS` (default 30)

**7c.** If send fails: wait 60s, retry once

**7d.** If retry also fails:
- Save summary to `AI_Employee_Vault/Pending_Approval/WHATSAPP_briefing_YYYYMMDD_HHMMSS.md`
- Log result as `whatsapp_queued_for_approval`
- Continue (do NOT abort briefing generation over WhatsApp failure)

**7e.** On success: log `whatsapp_sent`

### Step 10 — Log completion to gold_tier_progress.md

Append this entry to `AI_Employee_Vault/Logs/gold_tier_progress.md`:
```markdown
| YYYY-MM-DD HH:MM | audit_complete | Ns | health=X | revenue=$Y | tasks=N | WoW: revenue +/-Z% |
```

If runtime exceeds `max_runtime` (10 min): log `WARNING: runtime exceeded` but do NOT kill the process.

> ⚠️ NOTE: Log retention (purge logs older than 90 days) is handled by `src/log_janitor.py`.
> Do NOT add purge logic to this skill or to `audit_generator.py`.
> Log janitor runs 30 minutes after this skill (cron: `30 23 * * 0`).

---

## Required .env Variables

```bash
# CEO Briefing — Required
OWNER_WHATSAPP_NUMBER=447911123456
WHATSAPP_SESSION_PATH=/secure/path/to/session
WHATSAPP_SEND_TIMEOUT_SECONDS=30

# CEO Briefing — Thresholds
BRIEFING_ALERT_INVOICE_OVERDUE_DAYS=30
BRIEFING_ALERT_TRANSACTION_THRESHOLD=500
BRIEFING_SUBSCRIPTION_INACTIVE_DAYS=30

# Odoo (optional — briefing degrades gracefully if missing)
ODOO_URL=http://localhost:8069
ODOO_DB=mycompany
ODOO_USERNAME=admin
ODOO_PASSWORD=           # prefer: use OS keychain or secrets manager
```

---

## Success Criteria

- `CEO_BRIEFING_YYYYMMDD_HHMMSS.md` exists in `/Vault/Briefings/` within 60s of trigger
- `CEO_BRIEFING_LATEST.md` always reflects the most recent successful run
- Briefing contains all 7 required section headers with non-empty content
- `## Financial Summary` contains at least one numeric value
- Dashboard.md `Last CEO Briefing` line is updated
- WhatsApp message delivered (`whatsapp_sent`) OR queued (`whatsapp_queued_for_approval`)
- `gold_tier_progress.md` updated with `audit_complete` + runtime in seconds
- If validation fails: `DRAFT` file + `ALERT_briefing_incomplete_*.md` created

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Missing vault folder | count=0, continue |
| `Business_Goals.md` missing | Use `monthly_goal=0`, skip WoW revenue comparison |
| Odoo offline | Use exact placeholder text (see Step 3) |
| No previous briefing (first run) | WoW columns show "N/A (first run)" |
| WhatsApp credentials missing | Log `whatsapp_skipped`, continue |
| WhatsApp send fails | Retry once after 60s; then queue to Pending_Approval/ |
| Validation fails | Save as DRAFT, create alert, do NOT send WhatsApp |
| Disk full on write | Raise immediately with clear message |
| Runtime > 10 min | Log WARNING, continue to completion |

---

## Cron Setup

```bash
# Sunday 11 PM — CEO Briefing
0 23 * * 0 cd /path/to/project && uv run zoya-audit

# Sunday 11:30 PM — Log Janitor (ALWAYS runs AFTER CEO Briefing)
30 23 * * 0 cd /path/to/project && uv run python -m src.log_janitor
```

---

## CLI

```bash
# Normal weekly run
uv run zoya-audit

# Force run any day
uv run zoya-audit --force

# Dry run (no WhatsApp, no file writes)
uv run zoya-audit --dry-run --force

# Regenerate briefing for a past week (backfill)
uv run zoya-audit --force --date 2026-02-10

# Verbose output (print briefing to stdout as well)
uv run zoya-audit --force --verbose
```
