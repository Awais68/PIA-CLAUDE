# Zoya - Agent Architecture

## Overview

Zoya is a Personal AI Employee built on Claude Code + Obsidian. She manages both personal and freelance/consulting business operations autonomously using a local-first, file-driven architecture.

**Tier:** Gold
**Architecture:** Perception -> Orchestration -> Reasoning -> Action (file-based)

---

## System Components

### 1. The Brain (Claude Code)

Claude Code is the reasoning engine. It reads from the Obsidian vault, thinks about what needs to be done, and writes results back. All AI functionality is implemented as **Agent Skills** (`.claude/skills/`).

Claude Code operates in this loop:
1. **Read** - Process the file provided by the orchestrator
2. **Think** - Analyze the content, determine type and priority
3. **Plan** - Decide actions: summarize, extract tasks, categorize
4. **Write** - Write processed output to the metadata file
5. **Return** - Hand control back to the orchestrator for file movement

### 2. The Memory/GUI (Obsidian Vault)

The Obsidian vault at `./AI_Employee_Vault/` serves as:
- **Dashboard** - Real-time status via `Dashboard.md`
- **Rules Engine** - Business rules via `Company_Handbook.md`
- **Task Queue** - File-based job queue via folder structure
- **Audit Trail** - All processed items archived in `/Done/`

### 3. The Senses (File System Watcher)

A Python watcher script (`src/watcher.py`) monitors `/Inbox/` for new files. When a file appears:
1. Watcher detects the new file via `watchdog` library
2. **Waits for file stability** (size stops changing — handles large copies)
3. **Filters** unsupported types and OS junk files (.DS_Store, etc.)
4. **Rejects** files over the size limit (default 10 MB)
5. **Deduplicates** via SHA-256 content hash (same file dropped twice = ignored)
6. Creates a **timestamped** metadata `.md` file in `/Needs_Action/`
7. Copies the original file alongside the metadata (timestamped name prevents collisions)
8. Removes the original from `/Inbox/`

**Supported file types:**
- `.pdf` - Contracts, invoices, receipts, proposals
- `.docx` - Documents, letters, reports
- `.md` - Notes, task lists, meeting notes
- All others - Moved to `/Quarantine/` with a reason file

### 4. The Orchestrator (`src/orchestrator.py`)

The orchestrator is the **missing link** between the watcher and Claude Code. It:
1. **Acquires a process lock** (PID file) — only one orchestrator runs at a time
2. **Polls** `/Needs_Action/` for metadata files with `status: pending`
3. **Claims** a file by moving it + companion to `/In_Progress/` (claim-by-move)
4. **Invokes Claude Code** via CLI with the inbox-processor skill prompt
5. On **success**: moves files to `/Done/`, updates frontmatter
6. On **failure**: increments `retry_count`, moves back to `/Needs_Action/`
7. After **MAX_RETRIES** (default 3): moves to `/Quarantine/`
8. **Triggers dashboard-updater** skill after each processing batch

This solves the "5 files at once" problem: files are processed sequentially, one at a time, with claim-by-move preventing any race conditions.

---

## Vault Folder Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status overview
├── Company_Handbook.md        # Rules of engagement for Zoya
│
├── Inbox/                     # Drop folder - monitored by File System Watcher
│   └── (drop files here)
│
├── Needs_Action/              # Queue - items waiting for orchestrator to claim
│   ├── FILE_<timestamp>_<name>.md     # Metadata file
│   └── FILE_<timestamp>_<name>.pdf    # Original file copy
│
├── In_Progress/               # Claimed - currently being processed by Claude
│   └── (one file at a time, moved here by orchestrator)
│
├── Done/                      # Archive - completed items
│   └── FILE_<timestamp>_<name>.md     # Processed with summary + actions
│
├── Quarantine/                # Failed items - need manual review
│   ├── Q_<timestamp>_<name>.pdf       # The file that failed
│   └── Q_<timestamp>_<name>.pdf.reason.md  # Why it was quarantined
│
└── Logs/                      # Audit trail
    ├── YYYY-MM-DD.log         # Human-readable log
    └── YYYY-MM-DD.json        # Structured JSON-lines log
```

---

## File Lifecycle

```
User drops file into /Inbox/
        |
        v
Watcher detects new file (watchdog on_created)
        |
        v
Wait for file stability (size stops changing, 2s intervals)
        |
        +--[Unstable/Junk/Too large/Wrong type]--> /Quarantine/ + reason
        |
        v
Compute SHA-256 hash
        |
        +--[Duplicate hash]--> Delete from Inbox (skip)
        |
        v
Copy to /Needs_Action/ with timestamped name + write metadata .md
Delete original from /Inbox/
        |
        v
Orchestrator polls /Needs_Action/ (every 5 seconds)
        |
        v
Claim: move metadata + file to /In_Progress/ (atomic claim-by-move)
        |
        v
Invoke Claude Code (inbox-processor skill)
        |
        +--[Success]--> Move to /Done/, update frontmatter
        |
        +--[Failure]--> Increment retry_count
        |                   |
        |                   +--[retries < 3]--> Move back to /Needs_Action/
        |                   |
        |                   +--[retries >= 3]--> Move to /Quarantine/
        |
        v
Dashboard-updater skill refreshes Dashboard.md
        |
        v
User reviews in Obsidian
```

---

## Agent Skills

All AI functionality is implemented as Claude Code Agent Skills. Each skill is a self-contained module in `.claude/skills/`.

### Skill 1: `inbox-processor`

**Trigger:** Orchestrator invokes Claude with a specific file path
**Actions:**
- Read the document (PDF/DOCX/Markdown)
- Generate a concise 2-3 sentence summary
- Extract action items (deadlines, tasks, follow-ups)
- Categorize the document (invoice, contract, proposal, receipt, note, other)
- Assign priority (high/medium/low)
- Write processed results back to the metadata file
- Does NOT move files (orchestrator handles movement)

**Output format (written to the metadata .md file):**
```markdown
---
type: <invoice|contract|proposal|receipt|note|other>
original_name: <filename>
queued_name: <timestamped filename>
size_bytes: <file size>
content_hash: <sha256>
queued_at: <ISO timestamp>
status: done
retry_count: <number>
priority: <high|medium|low>
processed_at: <ISO timestamp>
---

## Summary
<2-3 sentence summary of the document>

## Action Items
- [ ] <extracted action 1>
- [ ] <extracted action 2>

## Category
<why this categorization was chosen>
```

### Skill 2: `dashboard-updater`

**Trigger:** After any processing batch completes
**Actions:**
- Count files in each folder (Inbox, Needs_Action, In_Progress, Done, Quarantine)
- Read the 10 most recent Done/ items for the activity table
- List any quarantined items as alerts
- Overwrite `Dashboard.md` with current state

### Skill 3: `vault-init`

**Trigger:** Manual - first-time setup
**Actions:**
- Create the full folder structure
- Generate initial `Dashboard.md` from template
- Generate initial `Company_Handbook.md` from template
- Verify all paths exist
- Idempotent — safe to run multiple times

---

## Edge Cases Handled

| Edge Case | How It's Handled |
|-----------|-----------------|
| 5 files dropped at once | Watcher queues all 5 independently; orchestrator processes one at a time via claim-by-move |
| Duplicate file | SHA-256 content hash deduplication in watcher; second copy silently skipped |
| Large file still copying | Watcher waits for file stability (size unchanged for 3 consecutive checks at 2s intervals) |
| Unsupported file type (.xlsx, .png) | Moved to /Quarantine/ with reason file |
| OS junk files (.DS_Store, thumbs.db) | Silently ignored by watcher |
| Filenames with spaces/unicode | Sanitised to alphanumeric + underscore, capped at 80 chars |
| Claude Code crashes mid-processing | File stays in /In_Progress/; orchestrator retries on next cycle (moves back to Needs_Action) |
| Claude fails 3 times | File moved to /Quarantine/ with failure reason |
| Two orchestrators started | PID-based lock file prevents second instance |
| Watcher crashes | Stateless — restart picks up where it left off; existing Needs_Action hashes reloaded |
| Scanned/image-only PDF | Claude reports "manual review required" in summary |
| Password-protected file | Claude reports "could not be read" in summary |
| Disk full | Write operations fail with OS error; logged; file stays in current folder |
| /Done/ grows to 10,000 files | Dashboard only reads 10 most recent |
| Corrupt YAML frontmatter | Regex-based parser degrades gracefully (returns empty dict) |

---

## Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│   /Inbox/   │────>│   Watcher    │────>│/Needs_Action/│────>│Orchestrator│
│ (drop zone) │     │ (src/watcher)│     │  (queue)     │     │(src/orch.) │
└─────────────┘     └──────────────┘     └──────────────┘     └─────┬──────┘
                         │                                          │
                         │ unsupported/                    claim-by-move
                         │ too large                                │
                         v                                          v
                    ┌──────────┐                           ┌──────────────┐
                    │/Quarantine│                           │/In_Progress/ │
                    │(failures) │                           │ (claimed)    │
                    └──────────┘                           └──────┬───────┘
                         ^                                        │
                         │ max retries                   Claude Code CLI
                         │                                        │
                         │                              ┌─────────┴────────┐
                         │                              │                  │
                         │                          success            failure
                         │                              │                  │
                         │                              v                  v
                         │                        ┌──────────┐    retry_count++
                         │                        │  /Done/   │        │
                         │                        │ (archive) │        │
                         │                        └──────────┘   back to queue
                         │                              │         or quarantine
                         │                              v
                         │                     ┌─────────────────┐
                         └─────────────────────│Dashboard.md     │
                                               │ (updated)       │
                                               └─────────────────┘
```

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Reasoning Engine | Claude Code (Opus) | Document analysis, summarization, categorization |
| Knowledge Base | Obsidian (local Markdown) | Dashboard, rules, file storage |
| File Watcher | Python + watchdog (uv) | Monitor /Inbox/ for new files |
| Orchestrator | Python (uv) | Queue management, Claude invocation, file lifecycle |
| Package Manager | uv | Python dependency management |
| Agent Skills | Claude Code Skills | Modular AI functionality |
| Version Control | Git | Track vault and code changes |

---

## Running Zoya

### First-time setup

```bash
# 1. Install dependencies
uv sync

# 2. Initialize the vault (if not already done)
claude "Initialize the Zoya vault using the vault-init skill"
```

### Start the system

Run in **two separate terminals**:

```bash
# Terminal 1: Start the file watcher
uv run python -m src.watcher

# Terminal 2: Start the orchestrator
uv run python -m src.orchestrator
```

### Process a file

```bash
# Drop a file into the Inbox
cp ~/Documents/invoice.pdf AI_Employee_Vault/Inbox/

# Watch the terminals — watcher picks it up, orchestrator processes it
# Check the result in Obsidian or:
cat AI_Employee_Vault/Done/FILE_*_invoice.md
```

---

## Logging

Every action is logged in two formats:

1. **Human-readable** (`Logs/YYYY-MM-DD.log`):
   ```
   2026-02-14T10:30:00 [orchestrator] INFO: Invoking Claude Code for: invoice.pdf
   ```

2. **Structured JSON-lines** (`Logs/YYYY-MM-DD.json`):
   ```json
   {"timestamp":"2026-02-14T10:30:00Z","action_type":"file_done","actor":"zoya","target":"Done/FILE_20260214_103000_invoice.md","parameters":{},"result":"success"}
   ```

---

## Security Notes

- No credentials needed for Bronze tier (file system watcher only)
- All data stays local (no API calls to external services beyond Claude)
- Vault is Git-tracked but `.env` and secrets are in `.gitignore`
- Logs provide audit trail of all AI actions
- PID-based locking prevents concurrent processing corruption

---

## Gold Tier — Active Features

### G1: CEO Briefing Generator (`src/briefing_generator.py`)
- Daily/weekly briefing documents in `AI_Employee_Vault/Briefings/`
- Aggregates Done/, Pending/, Quarantine/ data across all channels
- Channel breakdown (file_drop / gmail / whatsapp)
- System health score (0-100)
- Entry point: `uv run zoya-briefing [--weekly]`

### G2: Ralph Wiggum Loop (`src/ralph_loop.py`)
- Self-monitoring: detects stuck In_Progress, high quarantine, stale pending
- Creates `RALPH_*.md` alert files in `Pending_Approval/` for human review
- Runs every orchestrator cycle (transparent, non-blocking)
- `get_system_status()` returns health dict for dashboard

### G3: Cross-Domain Contact Linker (`src/cross_domain_linker.py`)
- Links Gmail senders + WhatsApp contacts into `AI_Employee_Vault/Contacts/`
- `CONTACT_<key>.md` per unique identity (email / phone)
- Records full interaction history across channels
- Called automatically after each item is processed

### G4: Gold Dashboard
- System health score line
- Briefings + Contacts folder counts
- Full channel breakdown (file_drop / gmail / whatsapp)

### G5: Cross-Domain Orchestrator (`src/cross_domain_orchestrator.py`)
- Bridges personal and business domains automatically
- **Bridge 1:** WhatsApp messages containing business keywords (invoice, payment, project, client, etc.)
  → auto-creates `TASK_*.md` in `Business/Tasks/`
- **Bridge 2:** Bank transaction items in Done/ with payee matching a client
  → appends ledger row to matching `Clients/CLIENT_*.md`
- Deduplication via `Logs/.cross_domain_processed.json` (no double-processing)
- Entry point: `uv run zoya-cross-domain`
- Skill: `.claude/skills/cross-domain-integration/SKILL.md`

### G6: Odoo Community MCP Server (`src/mcp_servers/odoo_mcp.py`)
- Exposes Odoo ERP as MCP tools for Claude Code
- Uses Odoo XML-RPC API (Python stdlib `xmlrpc.client` — no extra deps)
- **Read tools (safe):** `odoo_test_connection`, `odoo_list_customers`,
  `odoo_list_invoices`, `odoo_list_projects`, `odoo_list_tasks`, `odoo_get_record`
- **Write tools (HITL):** `odoo_create_invoice`, `odoo_create_task`, `odoo_send_invoice`
  → all write ops route through `Pending_Approval/` before executing
- Config: `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD` in `.env`
- Entry point: `uv run zoya-odoo-mcp`

## Vault Folder Structure (Gold)
```
AI_Employee_Vault/
├── Briefings/         # CEO briefing documents (daily/weekly)
├── Contacts/          # Cross-channel contact records
├── Business/
│   └── Tasks/         # Auto-created tasks from WhatsApp business triggers
└── Clients/           # Client records with linked transaction ledgers
```

## Future Tiers

- **Platinum:** Cloud deployment + always-on operation
