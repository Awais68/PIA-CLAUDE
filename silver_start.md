# Zoya Silver Tier — How to Run & Test

**Project:** PIA-CLAUDE / Zoya Personal AI Employee
**Tier:** Silver (Gmail + WhatsApp + LinkedIn + MCP + HITL + Briefing)
**Tests:** 253/253 passing

---

## Quick Start (One Command)

```bash
./scripts/run_silver.sh
```

That's it. Opens 4 services in background, runs a demo test, and shows you the result.

---

## What Silver Tier Does

| Feature | Description |
|---------|-------------|
| File Watcher | Monitors `Inbox/` — detects any dropped PDF/DOCX/MD |
| Orchestrator | Picks up files, runs Claude AI, routes to Done/ or Pending_Approval/ |
| WhatsApp Watcher | Webhook server on port 5001, accepts test messages via curl |
| Gmail Watcher | Polls Gmail for unread emails, saves them to Inbox pipeline |
| LinkedIn Poster | Generates post drafts in DRY_RUN mode (no real posting) |
| Plan.md | Auto-creates a plan for invoices/contracts before processing |
| HITL Approval | High-priority items go to Pending_Approval/ for human review |
| CEO Briefing | Daily/weekly briefing doc with stats and health score |
| Ralph Monitor | Self-monitoring — detects stuck files and alerts you |
| Contact Linker | Links Gmail + WhatsApp contacts into Contacts/ folder |

---

## Prerequisites

```bash
# 1. Install uv (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install dependencies
cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"
uv sync

# 3. Verify services ready
uv run python scripts/test_credentials.py
```

Expected output:
```
[  OK]  AI Provider (Claude CLI)
[  OK]  LinkedIn API (DRY_RUN mode)
[  OK]  Vault folders
```

---

## Manual Start — 3 Terminals

### Terminal 1: File Watcher
```bash
cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"
uv run zoya-watcher
```
Watches `AI_Employee_Vault/Inbox/` for new files.

### Terminal 2: Orchestrator
```bash
cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"
uv run zoya-orchestrator
```
Processes files with Claude AI every 30 seconds.

### Terminal 3: WhatsApp Watcher
```bash
cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"
uv run zoya-whatsapp
```
Starts webhook server at `http://localhost:5001`

---

## All 7 Tests — Run These Yourself

### Test 1: Drop a File (Core Pipeline)

```bash
# Drop ANY pdf, docx, or md file into Inbox
cp ~/Documents/any_file.pdf "AI_Employee_Vault/Inbox/"

# Watch it move: Inbox → Needs_Action → In_Progress → Done
watch -n 2 'ls AI_Employee_Vault/Needs_Action/ AI_Employee_Vault/In_Progress/ AI_Employee_Vault/Done/'

# Read the AI result
cat AI_Employee_Vault/Done/FILE_*.md | head -50
```

**What happens:** File detected in ~1s, Claude processes it in ~30s, result in Done/ with summary + action items.

---

### Test 2: Drop a Meeting Note / Invoice

```bash
cat > "AI_Employee_Vault/Inbox/meeting_notes.md" << 'EOF'
# Client Meeting — Feb 2026

Attendees: Awais, Sarah (TechCorp)

Action Items:
- [ ] Send contract by Feb 25 — deadline!
- [ ] Invoice for $2,500 due March 1
- [ ] Follow up on Phase 2 proposal

Budget approved: $15,000
EOF
```

Watch for:
- `Plans/` folder — a Plan.md gets auto-created (invoice/contract detected)
- `Pending_Approval/` — if Claude flags it as high priority

---

### Test 3: WhatsApp Message (No Real WhatsApp Needed)

```bash
# Send a fake WhatsApp message
curl -X POST http://localhost:5001/test-message \
  -H "Content-Type: application/json" \
  -d '{"from": "+923001234567", "message": "Please process the invoice I sent you yesterday", "type": "text"}'

# It lands in Needs_Action with source: whatsapp
ls AI_Employee_Vault/Needs_Action/
# Shows: FILE_*_WHATSAPP_*.md

# Process it immediately
uv run zoya-orchestrator --once
```

Check the WhatsApp watcher health:
```bash
curl http://localhost:5001/health
```

---

### Test 4: Single-Cycle Processing (--once mode)

```bash
# Process everything currently in queue, then exit
# Perfect for cron jobs or instant testing
uv run zoya-orchestrator --once
```

---

### Test 5: LinkedIn Post Generation

```bash
uv run zoya-linkedin

# Check the generated draft
ls AI_Employee_Vault/Pending_Approval/LINKEDIN_*.md
cat AI_Employee_Vault/Pending_Approval/LINKEDIN_*.md
```

DRY_RUN mode is on by default — drafts are saved but NOT posted to LinkedIn.

---

### Test 6: CEO Daily Briefing

```bash
# Generate today's briefing
uv run zoya-briefing

# See the briefing
cat AI_Employee_Vault/Briefings/BRIEFING_*.md

# Generate weekly briefing
uv run zoya-briefing --weekly
```

---

### Test 7: HITL Approval Flow

When a high-priority invoice/contract lands in `Pending_Approval/`, simulate human approval:

```bash
# Approve — moves to Done on next cycle
mv AI_Employee_Vault/Pending_Approval/FILE_*.md AI_Employee_Vault/Approved/
uv run zoya-orchestrator --once

# Reject — also moves to Done with rejected status
mv AI_Employee_Vault/Pending_Approval/FILE_*.md AI_Employee_Vault/Rejected/
uv run zoya-orchestrator --once
```

---

## System Health Check

```bash
# Check Ralph Wiggum monitor (self-monitoring)
python3 -c "
from src.ralph_loop import get_system_status
import json
print(json.dumps(get_system_status(), indent=2))
"
```

Expected output (healthy system):
```json
{
  "status": "ok",
  "issues": 0,
  "stuck_in_progress": 0,
  "quarantine_count": 0,
  "approval_backlog": 0,
  "stale_pending": 0
}
```

---

## Live Log Watching

```bash
# Follow all events in real-time
tail -f "AI_Employee_Vault/Logs/$(date +%Y-%m-%d).log"
```

---

## Vault Folder Reference

| Folder | What's Inside |
|--------|--------------|
| `Inbox/` | Drop files here — empties within 2 seconds |
| `Needs_Action/` | Queue — waiting for orchestrator to pick up |
| `In_Progress/` | Being processed by Claude RIGHT NOW |
| `Done/` | Finished — open any `.md` to read the AI summary |
| `Pending_Approval/` | Needs your review (invoices, contracts, LinkedIn posts) |
| `Approved/` | You approved → orchestrator moves to Done |
| `Rejected/` | You rejected → orchestrator archives to Done |
| `Plans/` | Auto-generated plans for invoices/contracts |
| `Briefings/` | CEO daily/weekly briefing documents |
| `Contacts/` | Cross-channel contact records (Gmail + WhatsApp) |
| `Quarantine/` | Files that failed 3 times — need manual fix |
| `Logs/` | Full audit trail — JSON + human-readable |
| `Dashboard.md` | Live status — open in Obsidian or cat it |

---

## Entry Points Reference

```bash
uv run zoya-watcher          # File system watcher (Inbox monitor)
uv run zoya-orchestrator     # Main processor (add --once for single run)
uv run zoya-whatsapp         # WhatsApp webhook server (port 5001)
uv run zoya-gmail            # Gmail watcher (polls every 60s)
uv run zoya-linkedin         # LinkedIn post generator (DRY_RUN)
uv run zoya-email-mcp        # Email MCP server (for Claude integration)
uv run zoya-briefing         # CEO briefing generator (add --weekly)
```

---

## Crontab (Automated Scheduling)

```bash
# Edit your crontab
crontab -e
```

Add these lines:
```cron
# Process queue every 5 minutes
*/5 * * * *  cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE" && uv run zoya-orchestrator --once >> /tmp/zoya_cron.log 2>&1

# Daily CEO briefing at 8:00 AM
0 8 * * *    cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE" && uv run zoya-briefing >> /tmp/zoya_briefing.log 2>&1

# Weekly briefing every Monday at 9:00 AM
0 9 * * 1    cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE" && uv run zoya-briefing --weekly >> /tmp/zoya_briefing.log 2>&1
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| File stays in Inbox | Check `uv run zoya-watcher` is running |
| File stuck in Needs_Action | Check `uv run zoya-orchestrator` is running |
| File stuck in In_Progress > 15 min | Ralph will create an alert in Pending_Approval/ |
| Claude fails | Check `claude --version` works in terminal |
| Port 5001 in use | `kill $(lsof -t -i:5001)` then restart zoya-whatsapp |
| Quarantine items | Read the reason: `cat AI_Employee_Vault/Quarantine/*.reason.md` |
| Run tests | `uv run pytest tests/ -v` — should show 253 passed |
