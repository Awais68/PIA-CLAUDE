# Silver Tier Implementation Blueprint - Zoya

**Version:** 1.0
**Date:** 2026-02-14
**Author:** Generated from codebase analysis
**Prerequisite:** Bronze Tier COMPLETE (69 tests passing, all 5/5 requirements met)

---

## 1. Executive Summary

### Current State (Bronze - DONE)

| Component | Status | Details |
|-----------|--------|---------|
| File System Watcher | COMPLETE | `src/watcher.py` — watchdog-based, dedup, stability checks, quarantine |
| Orchestrator | COMPLETE | `src/orchestrator.py` — claim-by-move, retry logic, Claude invocation |
| Obsidian Vault | COMPLETE | Dashboard.md, Company_Handbook.md, 6 folders |
| Agent Skills | COMPLETE | 3 skills: inbox-processor, dashboard-updater, vault-init |
| Tests | COMPLETE | 69 tests across 4 files (config, utils, watcher, orchestrator) |
| Logging | COMPLETE | Dual format: human-readable `.log` + structured `.json` |

### Target State (Silver)

| Requirement | ID | What's Needed |
|-------------|----|----|
| Two+ additional Watchers | S2 | Gmail Watcher + WhatsApp or LinkedIn watcher |
| LinkedIn Auto-Posting | S3 | Generate + post business content to LinkedIn |
| Plan.md Reasoning Loop | S4 | Claude creates structured Plan.md for multi-step tasks |
| One MCP Server | S5 | External action capability (email sending) |
| HITL Approval Workflow | S6 | Pending_Approval flow for sensitive actions |
| Basic Scheduling | S7 | Cron/scheduler for automated task execution |
| All AI as Agent Skills | S8 | SKILL.md for every new AI feature |

### Timeline Estimate (24-32 hours realistic)

```
Phase 1: Foundation & Quick Wins ........  3-4 hours
Phase 2: Gmail Pipeline .................  6-8 hours
Phase 3: HITL Approval Workflow .........  4-5 hours
Phase 4: MCP Server .....................  4-5 hours
Phase 5: LinkedIn + Extra Watcher .......  5-7 hours
Phase 6: Scheduling & Polish ............  2-3 hours
                                          ─────────
                                          24-32 hours
```

---

## 2. Architecture Design

### 2.1 System Components (Silver Target)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SILVER TIER ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL SOURCES                               │
├──────────────┬──────────────┬───────────────┬───────────────────────────┤
│   Gmail API  │  WhatsApp    │   LinkedIn    │   Local File System       │
│   (OAuth2)   │  (Twilio)    │   (API/MCP)   │   (watchdog)              │
└──────┬───────┴──────┬───────┴───────┬───────┴───────────┬───────────────┘
       │              │               │                   │
       ▼              ▼               ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       PERCEPTION LAYER (Watchers)                       │
│                                                                         │
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ gmail_watcher│ │whatsapp_watch │ │linkedin_poster│ │   watcher    │  │
│  │   (NEW)      │ │   (NEW)       │ │    (NEW)      │ │  (EXISTING)  │  │
│  │ src/gmail_   │ │ src/whatsapp_ │ │ src/linkedin_ │ │ src/watcher  │  │
│  │ watcher.py   │ │ watcher.py    │ │ _poster.py    │ │ .py          │  │
│  └──────┬───────┘ └──────┬────────┘ └──────┬────────┘ └──────┬───────┘  │
│         │                │                  │                 │          │
│         └────────────────┴──────────────────┴────────┬────────┘          │
└──────────────────────────────────────────────────────┼──────────────────┘
                                                       │
                                               All write to
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        OBSIDIAN VAULT (Local-First)                     │
│                                                                         │
│  ┌─────────┐ ┌──────────────┐ ┌─────────────┐ ┌─────────┐              │
│  │ /Inbox/ │ │/Needs_Action/│ │/In_Progress/ │ │ /Done/  │              │
│  └────┬────┘ └──────┬───────┘ └──────┬───────┘ └─────────┘              │
│       │             │                │                                   │
│  ┌────┴─────────────┴────────────────┴──────────────────────────────┐   │
│  │ NEW FOLDERS:                                                      │   │
│  │ /Plans/              — Plan.md files from reasoning loop          │   │
│  │ /Pending_Approval/   — Items awaiting human decision              │   │
│  │ /Approved/           — Human-approved items                       │   │
│  │ /Rejected/           — Human-rejected items                       │   │
│  │ /Briefings/          — Scheduled briefing outputs                 │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Dashboard.md  │  Company_Handbook.md  │  /Quarantine/  │  /Logs/       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER (Enhanced)                        │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  src/orchestrator.py (MODIFIED)                   │   │
│  │                                                                   │   │
│  │  Existing:                    New:                                 │   │
│  │  - Poll /Needs_Action/        - Plan.md creation (S4)             │   │
│  │  - Claim-by-move              - HITL routing (S6)                 │   │
│  │  - Claude invocation          - Poll /Approved/ & /Rejected/      │   │
│  │  - Retry + quarantine         - --once flag for cron (S7)         │   │
│  │  - Dashboard update           - Source-aware processing           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    Claude Code invocation
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       REASONING LAYER (Claude Code)                     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      Agent Skills                                │   │
│  │                                                                   │   │
│  │  EXISTING:                    NEW:                                 │   │
│  │  - inbox-processor            - plan-creator (S4)                 │   │
│  │  - dashboard-updater          - hitl-evaluator (S6)               │   │
│  │  - vault-init                 - gmail-processor (S2)              │   │
│  │                               - whatsapp-processor (S2)           │   │
│  │                               - linkedin-poster (S3)              │   │
│  │                               - scheduled-briefing (S7)           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                         For external actions
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        ACTION LAYER (NEW)                               │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    MCP Server: email-mcp (S5)                    │   │
│  │                                                                   │   │
│  │  Tools:                                                           │   │
│  │  - send_email(to, subject, body)                                  │   │
│  │  - search_emails(query)                                           │   │
│  │  - draft_reply(message_id, body)                                  │   │
│  │                                                                   │   │
│  │  All sends require HITL approval first                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              Human-in-the-Loop Gate (S6)                         │   │
│  │                                                                   │   │
│  │  /Pending_Approval/ ──[user reviews in Obsidian]──> /Approved/   │   │
│  │                                                 └──> /Rejected/  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     SCHEDULING LAYER (NEW - S7)                         │
│                                                                         │
│  cron / systemd timer                                                   │
│  - Daily dashboard refresh (8:00 AM)                                    │
│  - Periodic orchestrator --once (every 15 min)                          │
│  - Weekly briefing generation (Monday 8:00 AM)                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow (Silver)

```
                    ┌─────────────┐
                    │  Gmail API  │
                    └──────┬──────┘
                           │ Poll every 120s
                           ▼
                    ┌──────────────┐        ┌───────────────┐
                    │gmail_watcher │───────>│               │
                    │  (new)       │  .md   │               │
                    └──────────────┘  to    │               │
                                     Inbox  │   /Inbox/     │
┌──────────────┐                     ──────>│               │
│ File drop    │────────────────────────────│               │
│ (existing)   │                            │               │
└──────────────┘                            └───────┬───────┘
                                                    │
                    ┌───────────────┐                │ (existing watcher.py)
                    │WhatsApp/Twilio│                │
                    │  webhook      │                ▼
                    └───────┬───────┘        ┌──────────────┐
                            │               │/Needs_Action/ │
                            │ .md to Inbox  │              │
                            └──────────────>│              │
                                            └───────┬──────┘
                                                    │
                                          orchestrator.py
                                           (claim-by-move)
                                                    │
                                    ┌───────────────┼───────────────┐
                                    │               │               │
                                    ▼               ▼               ▼
                             ┌────────────┐  ┌───────────┐  ┌────────────┐
                             │ plan-creator│  │  inbox-   │  │   hitl-    │
                             │   skill     │  │ processor │  │ evaluator  │
                             │   (S4)      │  │ (existing)│  │   (S6)     │
                             └─────┬──────┘  └─────┬─────┘  └─────┬──────┘
                                   │               │              │
                                   ▼               │              ▼
                            ┌────────────┐         │      ┌──────────────┐
                            │  /Plans/   │         │      │/Pending_     │
                            │  Plan.md   │         │      │ Approval/    │
                            └────────────┘         │      └──────┬───────┘
                                                   │             │
                                                   │      [user reviews]
                                                   │             │
                                            ┌──────┴──────┐      │
                                            │             │      │
                                            ▼             ▼      ▼
                                       ┌─────────┐  ┌──────────────┐
                                       │ /Done/  │  │ /Approved/   │
                                       └─────────┘  └──────┬───────┘
                                                           │
                                                    MCP email-server
                                                           │
                                                    ┌──────┴───────┐
                                                    │ Send email / │
                                                    │ External act │
                                                    └──────────────┘
```

### 2.3 File Structure Changes

New files and folders added for Silver (marked with `(NEW)`):

```
PIA-CLAUDE/
├── pyproject.toml                          # MODIFIED: new dependencies
├── Silver_Tier_Blueprint.md                # (NEW) this file
│
├── src/
│   ├── __init__.py
│   ├── config.py                           # MODIFIED: new paths + settings
│   ├── utils.py                            # MODIFIED: new helpers
│   ├── watcher.py                          # UNCHANGED (Bronze)
│   ├── orchestrator.py                     # MODIFIED: Plan.md, HITL, --once
│   ├── gmail_watcher.py                    # (NEW) S2 - Gmail polling
│   ├── whatsapp_watcher.py                 # (NEW) S2 - WhatsApp webhook
│   ├── linkedin_poster.py                  # (NEW) S3 - LinkedIn posting
│   ├── scheduler.py                        # (NEW) S7 - scheduling logic
│   └── mcp/                                # (NEW) S5 - MCP servers
│       ├── __init__.py
│       └── email_server.py                 # (NEW) Gmail MCP server
│
├── .claude/
│   ├── settings.local.json                 # MODIFIED: new permissions
│   ├── mcp.json                            # (NEW) MCP server config
│   └── skills/
│       ├── inbox-processor/SKILL.md        # UNCHANGED
│       ├── dashboard-updater/SKILL.md      # UNCHANGED
│       ├── vault-init/SKILL.md             # UNCHANGED
│       ├── plan-creator/SKILL.md           # (NEW) S4
│       ├── hitl-evaluator/SKILL.md         # (NEW) S6
│       ├── gmail-processor/SKILL.md        # (NEW) S2
│       ├── whatsapp-processor/SKILL.md     # (NEW) S2
│       ├── linkedin-poster/SKILL.md        # (NEW) S3
│       └── scheduled-briefing/SKILL.md     # (NEW) S7
│
├── AI_Employee_Vault/
│   ├── Dashboard.md                        # MODIFIED: new sections
│   ├── Company_Handbook.md                 # MODIFIED: HITL rules
│   ├── Inbox/                              # UNCHANGED
│   ├── Needs_Action/                       # UNCHANGED
│   ├── In_Progress/                        # UNCHANGED
│   ├── Done/                               # UNCHANGED
│   ├── Quarantine/                         # UNCHANGED
│   ├── Logs/                               # UNCHANGED
│   ├── Plans/                              # (NEW) S4 - reasoning output
│   │   └── .gitkeep
│   ├── Pending_Approval/                   # (NEW) S6 - awaiting human
│   │   └── .gitkeep
│   ├── Approved/                           # (NEW) S6 - human approved
│   │   └── .gitkeep
│   ├── Rejected/                           # (NEW) S6 - human rejected
│   │   └── .gitkeep
│   └── Briefings/                          # (NEW) S7 - scheduled output
│       └── .gitkeep
│
├── tests/
│   ├── conftest.py                         # MODIFIED: new fixtures
│   ├── test_config.py                      # MODIFIED: new path tests
│   ├── test_utils.py                       # UNCHANGED
│   ├── test_watcher.py                     # UNCHANGED
│   ├── test_orchestrator.py                # MODIFIED: HITL + Plan.md tests
│   ├── test_gmail_watcher.py               # (NEW)
│   ├── test_whatsapp_watcher.py            # (NEW)
│   ├── test_linkedin_poster.py             # (NEW)
│   ├── test_hitl.py                        # (NEW)
│   ├── test_plan_creator.py                # (NEW)
│   └── test_scheduler.py                   # (NEW)
│
├── scripts/                                # (NEW)
│   └── start_silver.sh                     # (NEW) launch all processes
│
├── credentials.json                        # (NEW, GITIGNORED) Google OAuth
└── token.json                              # (NEW, GITIGNORED) OAuth token
```

### 2.4 Integration Points

| Source | Writes To | Read By | Format |
|--------|-----------|---------|--------|
| gmail_watcher.py | `/Inbox/*.md` | watcher.py | Markdown with `source: gmail` frontmatter |
| whatsapp_watcher.py | `/Inbox/*.md` | watcher.py | Markdown with `source: whatsapp` frontmatter |
| watcher.py | `/Needs_Action/*.md` | orchestrator.py | Metadata with `status: pending` |
| orchestrator.py | `/Plans/*.md` | User (Obsidian) | Plan.md with steps + checkboxes |
| orchestrator.py | `/Pending_Approval/*.md` | User (Obsidian) | Approval request with decision prompt |
| User | `/Approved/*.md` | orchestrator.py | File moved = approval signal |
| orchestrator.py | MCP email_server | Gmail API | Tool call via MCP protocol |
| linkedin_poster.py | `/Pending_Approval/*.md` | User (Obsidian) | Post content for human review |
| cron | orchestrator.py `--once` | N/A | CLI invocation |

---

## 3. Phase-Based Implementation Plan

### Phase 1: Foundation & Quick Wins (3-4 hours)

**Goal:** Set up new vault folders, implement Plan.md reasoning loop, create SKILL.md stubs for all Silver features, and add the `--once` flag to the orchestrator for cron support.

#### Task 1.1: Create New Vault Folders (15 min)

**What:** Add Silver-tier folders to the vault.

**Changes to `src/config.py`:**
```python
# Add after existing path definitions:

# Silver Tier paths
PLANS = VAULT_PATH / "Plans"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"
APPROVED = VAULT_PATH / "Approved"
REJECTED = VAULT_PATH / "Rejected"
BRIEFINGS = VAULT_PATH / "Briefings"

# Gmail Watcher settings
GMAIL_POLL_INTERVAL = 120  # seconds
GMAIL_LABEL = "INBOX"
GMAIL_CREDENTIALS = PROJECT_ROOT / "credentials.json"
GMAIL_TOKEN = PROJECT_ROOT / "token.json"

# HITL settings
HITL_AMOUNT_THRESHOLD = 500  # dollars - invoices above this need approval
HITL_DEADLINE_DAYS = 7       # contracts with deadlines within this need approval

# LinkedIn settings
LINKEDIN_DRY_RUN = True  # safety default
```

**Folder creation:** Update `vault-init` skill or add to `config.py` startup.

```bash
mkdir -p AI_Employee_Vault/{Plans,Pending_Approval,Approved,Rejected,Briefings}
touch AI_Employee_Vault/{Plans,Pending_Approval,Approved,Rejected,Briefings}/.gitkeep
```

**Verification:** `ls AI_Employee_Vault/` shows all 11 folders.

---

#### Task 1.2: Implement Plan.md Reasoning Loop — S4 (2-3 hours)

**What:** Before processing complex documents, Claude creates a structured Plan.md in `/Plans/` showing its reasoning steps.

**New file: `.claude/skills/plan-creator/SKILL.md`**
```markdown
# Plan Creator Skill

## Purpose
Create a structured Plan.md file before processing complex multi-step tasks.
This demonstrates Claude's reasoning loop — think before acting.

## When to Create a Plan
Create a Plan.md when the document is:
- An invoice (payment actions needed)
- A contract (review + deadline tracking)
- A proposal (evaluation + response needed)
- Any document with priority: high

Do NOT create a Plan for:
- Simple notes or receipts (process directly)
- Documents with priority: low

## Input
- File path to the document being processed
- Metadata file path
- Original filename
- Document category (from initial scan)

## Plan.md Format
Write the plan to: AI_Employee_Vault/Plans/PLAN_<timestamp>_<filename>.md

---
created: <ISO 8601 timestamp>
task: <metadata filename>
source_file: <original filename>
document_type: <category>
status: in_progress
---

## Objective
<One sentence: what needs to be done with this document>

## Analysis
<2-3 sentences: what the document contains, key details found>

## Steps
- [x] Read and analyze document content
- [x] Identify document type: <type>
- [ ] Extract key fields (<list relevant fields for this type>)
- [ ] Determine priority level
- [ ] Check if human approval is required
- [ ] <Type-specific step, e.g., "Calculate payment deadline">
- [ ] Write processed results to metadata file

## Approval Required
<Yes/No — and why. Reference Company_Handbook.md thresholds>

## Estimated Complexity
<Low/Medium/High — based on document length and required actions>
```

**Changes to `src/orchestrator.py`:**

In the `process_with_claude()` function, add a two-phase invocation:
1. First call: Create Plan.md (plan-creator skill)
2. Second call: Process the file (inbox-processor skill — existing)

```python
def should_create_plan(meta_path: Path) -> bool:
    """Determine if this task warrants a Plan.md."""
    fm = _read_frontmatter(meta_path)
    doc_type = fm.get("type", "other")
    priority = fm.get("priority", "low")
    # Create plans for high-value document types
    return doc_type in ("invoice", "contract", "proposal") or priority == "high"


def create_plan(meta_path: Path, companion: Path | None) -> Path | None:
    """Invoke Claude to create a Plan.md for this task."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original = _read_frontmatter(meta_path).get("original_name", "unknown")
    stem = Path(original).stem
    plan_path = PLANS / f"PLAN_{timestamp}_{stem}.md"

    file_to_read = str(companion) if companion else str(meta_path)
    prompt = (
        f"You are Zoya. Use the plan-creator skill.\n\n"
        f"Create a Plan.md for processing this document.\n"
        f"**Document:** `{file_to_read}`\n"
        f"**Metadata:** `{meta_path}`\n"
        f"**Original filename:** {original}\n\n"
        f"Write the plan to: `{plan_path}`\n"
        f"Follow the exact format in the plan-creator skill.\n"
    )
    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions", prompt],
        capture_output=True, text=True, timeout=60, cwd=str(PROJECT_ROOT),
    )
    if result.returncode == 0 and plan_path.exists():
        logger.info(f"Plan created: {plan_path.name}")
        log_action("plan_created", str(plan_path), {"task": meta_path.name}, "success")
        return plan_path
    logger.warning(f"Plan creation failed (non-critical), proceeding without plan")
    return None
```

Modify `run_cycle()` to call `create_plan()` before `process_with_claude()`:

```python
# In run_cycle(), after claiming:
if should_create_plan(claimed_meta):
    create_plan(claimed_meta, claimed_companion)

success = process_with_claude(claimed_meta, claimed_companion)
```

**Testing:**
```python
# tests/test_plan_creator.py
def test_should_create_plan_for_invoice(vault, sample_md):
    """Plan created for invoice documents."""
    _update_frontmatter(sample_md, {"type": "invoice"})
    assert should_create_plan(sample_md) is True

def test_should_not_create_plan_for_note(vault, sample_md):
    """No plan for simple notes."""
    _update_frontmatter(sample_md, {"type": "note", "priority": "low"})
    assert should_create_plan(sample_md) is False

def test_plan_file_created(vault, sample_md, sample_companion):
    """Plan.md file written to /Plans/ folder."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Pre-create the plan file the mock would create
        plan_path = create_plan(sample_md, sample_companion)
        # Verify plan was attempted
        mock_run.assert_called_once()
```

**Success criteria:**
- [ ] Invoices, contracts, proposals trigger Plan.md creation
- [ ] Notes and receipts skip plan creation
- [ ] Plan.md written to `AI_Employee_Vault/Plans/` with correct format
- [ ] Plan creation failure does NOT block document processing
- [ ] Tests pass

---

#### Task 1.3: Add `--once` Flag to Orchestrator — S7 Prep (30 min)

**What:** Allow the orchestrator to run a single cycle and exit, enabling cron-based scheduling.

**Changes to `src/orchestrator.py`:**
```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="Zoya Orchestrator")
    parser.add_argument("--once", action="store_true",
                        help="Run one cycle and exit (for cron/scheduler use)")
    args = parser.parse_args()

    if not acquire_lock():
        logger.error("Another orchestrator is running. Exiting.")
        return
    atexit.register(release_lock)

    if args.once:
        logger.info("Running single cycle (--once mode)")
        processed = run_cycle()
        logger.info(f"Cycle complete. Processed {processed} files.")
        return

    # Existing continuous loop
    logger.info("Orchestrator started (continuous mode)")
    try:
        while True:
            run_cycle()
            time.sleep(ORCHESTRATOR_POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user")
```

**Testing:**
```python
def test_once_flag_exits_after_single_cycle(vault):
    """--once flag runs one cycle and returns."""
    with patch("src.orchestrator.run_cycle", return_value=0) as mock:
        # Simulate --once by calling main with args
        with patch("sys.argv", ["orchestrator", "--once"]):
            main()
        mock.assert_called_once()
```

---

#### Task 1.4: Create All SKILL.md Stubs — S8 (30 min)

**What:** Create skeleton SKILL.md files for every Silver feature.

Create these files (content filled in during each phase):
- `.claude/skills/plan-creator/SKILL.md` (done in Task 1.2)
- `.claude/skills/hitl-evaluator/SKILL.md`
- `.claude/skills/gmail-processor/SKILL.md`
- `.claude/skills/whatsapp-processor/SKILL.md`
- `.claude/skills/linkedin-poster/SKILL.md`
- `.claude/skills/scheduled-briefing/SKILL.md`

**Verification:** `ls .claude/skills/` shows 9 skill directories (3 existing + 6 new).

---

#### Phase 1 Dependencies
```
None — this phase has no external dependencies.
All tasks are internal code/file changes.
```

#### Phase 1 Success Criteria
- [ ] 5 new vault folders exist with .gitkeep files
- [ ] `config.py` has all Silver path constants
- [ ] Plan.md created for invoice/contract/proposal documents
- [ ] `--once` flag works on orchestrator
- [ ] 6 new SKILL.md stubs created
- [ ] All existing 69 tests still pass
- [ ] New tests for plan-creator pass

---

### Phase 2: Gmail Watcher (6-8 hours)

**Goal:** Implement a fully functional Gmail watcher that polls for new emails and feeds them into the existing pipeline.

#### Task 2.1: Google Cloud Project Setup (1 hour)

**What:** Create OAuth2 credentials for Gmail API access.

**Steps:**
1. Go to https://console.cloud.google.com
2. Create new project: "Zoya AI Employee"
3. Enable Gmail API:
   - APIs & Services > Library > Search "Gmail API" > Enable
4. Configure OAuth consent screen:
   - User Type: External (or Internal if using Google Workspace)
   - App name: "Zoya"
   - Scopes: `gmail.readonly`, `gmail.modify`, `gmail.send`
   - Test users: Add your email address
5. Create OAuth2 credentials:
   - APIs & Services > Credentials > Create > OAuth Client ID
   - Application type: **Desktop app**
   - Download as `credentials.json`
6. Place `credentials.json` in project root

**Verification:**
```bash
ls -la credentials.json        # File exists
grep credentials.json .gitignore  # Is gitignored
```

**Risk:** Google may require app verification for production use. Using "Desktop app" type + test user avoids this for development.

---

#### Task 2.2: Add Gmail Dependencies (15 min)

**What:** Install Google API client libraries.

```bash
uv add google-api-python-client google-auth-oauthlib google-auth-httplib2
```

**pyproject.toml additions:**
```toml
dependencies = [
    "watchdog>=6.0.0",
    "google-api-python-client>=2.100.0",
    "google-auth-oauthlib>=1.2.0",
    "google-auth-httplib2>=0.2.0",
]
```

**Verification:** `uv run python -c "from googleapiclient.discovery import build; print('OK')"`

---

#### Task 2.3: Implement Gmail Watcher (3-4 hours)

**New file: `src/gmail_watcher.py`**

```python
"""Gmail Watcher - polls Gmail for new emails and creates Inbox files."""

import time
import base64
from datetime import datetime
from pathlib import Path
from email.utils import parseaddr

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config import (
    INBOX, GMAIL_POLL_INTERVAL, GMAIL_CREDENTIALS, GMAIL_TOKEN,
    GMAIL_LABEL, PROJECT_ROOT,
)
from src.utils import setup_logger, log_action

logger = setup_logger("gmail_watcher")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def authenticate() -> Credentials:
    """Authenticate with Gmail API using OAuth2.

    First run opens a browser for consent. Subsequent runs use stored token.
    """
    creds = None

    if GMAIL_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GMAIL_CREDENTIALS.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {GMAIL_CREDENTIALS}. "
                    "Download from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GMAIL_CREDENTIALS), SCOPES
            )
            creds = flow.run_local_server(port=0)

        GMAIL_TOKEN.write_text(creds.to_json())
        logger.info("Gmail authentication successful, token saved")

    return creds


def get_service(creds: Credentials):
    """Build Gmail API service client."""
    return build("gmail", "v1", credentials=creds)


def fetch_unread_messages(service, max_results: int = 10) -> list[dict]:
    """Fetch unread messages from Gmail inbox."""
    results = service.users().messages().list(
        userId="me",
        q="is:unread",
        labelIds=[GMAIL_LABEL],
        maxResults=max_results,
    ).execute()
    return results.get("messages", [])


def get_message_detail(service, msg_id: str) -> dict:
    """Fetch full message details."""
    return service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()


def extract_headers(message: dict) -> dict[str, str]:
    """Extract common headers from a Gmail message."""
    headers = {}
    for header in message.get("payload", {}).get("headers", []):
        name = header["name"].lower()
        if name in ("from", "to", "subject", "date"):
            headers[name] = header["value"]
    return headers


def extract_body(message: dict) -> str:
    """Extract plain text body from a Gmail message."""
    payload = message.get("payload", {})

    # Simple message (no parts)
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # Multipart message
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

    # Fallback to snippet
    return message.get("snippet", "(No body content)")


def save_attachments(service, message: dict, msg_id: str) -> list[str]:
    """Download email attachments to /Inbox/."""
    saved = []
    payload = message.get("payload", {})

    for part in payload.get("parts", []):
        filename = part.get("filename")
        if not filename:
            continue

        att_id = part.get("body", {}).get("attachmentId")
        if not att_id:
            continue

        attachment = service.users().messages().attachments().get(
            userId="me", messageId=msg_id, id=att_id
        ).execute()

        data = base64.urlsafe_b64decode(attachment["data"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        dest = INBOX / f"GMAIL_{timestamp}_{safe_name}"
        dest.write_bytes(data)
        saved.append(str(dest))
        logger.info(f"Attachment saved: {dest.name}")

    return saved


def create_email_file(headers: dict, body: str, msg_id: str, attachments: list[str]) -> Path:
    """Create a markdown file in /Inbox/ representing the email."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _, from_email = parseaddr(headers.get("from", "Unknown"))
    subject = headers.get("subject", "No Subject")
    safe_subject = "".join(c if c.isalnum() or c in "_-" else "_" for c in subject)[:60]

    filepath = INBOX / f"EMAIL_{timestamp}_{safe_subject}.md"

    attachment_list = ""
    if attachments:
        attachment_list = "\n".join(f"- `{Path(a).name}`" for a in attachments)
        attachment_list = f"\n## Attachments\n{attachment_list}\n"

    content = f"""---
type: email
source: gmail
from: {headers.get('from', 'Unknown')}
to: {headers.get('to', 'Unknown')}
subject: {subject}
gmail_id: {msg_id}
received: {datetime.now().isoformat()}
status: pending
priority: medium
---

## Email Content

**From:** {headers.get('from', 'Unknown')}
**Subject:** {subject}
**Date:** {headers.get('date', 'Unknown')}

{body[:3000]}
{attachment_list}
## Suggested Actions
- [ ] Review email content
- [ ] Reply to sender
- [ ] Process any attachments
"""
    filepath.write_text(content)
    logger.info(f"Email file created: {filepath.name}")
    return filepath


def mark_as_read(service, msg_id: str):
    """Remove UNREAD label from a message."""
    service.users().messages().modify(
        userId="me", id=msg_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def poll_once(service, processed_ids: set) -> int:
    """Run one polling cycle. Returns count of new emails processed."""
    messages = fetch_unread_messages(service)
    count = 0

    for msg_summary in messages:
        msg_id = msg_summary["id"]
        if msg_id in processed_ids:
            continue

        try:
            message = get_message_detail(service, msg_id)
            headers = extract_headers(message)
            body = extract_body(message)
            attachments = save_attachments(service, message, msg_id)
            create_email_file(headers, body, msg_id, attachments)
            mark_as_read(service, msg_id)

            processed_ids.add(msg_id)
            count += 1

            log_action(
                "email_ingested",
                headers.get("subject", "Unknown"),
                {"from": headers.get("from", ""), "gmail_id": msg_id},
                "success",
            )
            logger.info(f"Processed email: {headers.get('subject', 'No Subject')}")

        except Exception as e:
            logger.error(f"Failed to process email {msg_id}: {e}")
            log_action("email_ingested", msg_id, {}, f"error: {e}")

    return count


def main():
    """Main entry point for Gmail watcher."""
    logger.info("Starting Gmail Watcher")
    logger.info(f"Poll interval: {GMAIL_POLL_INTERVAL}s")

    creds = authenticate()
    service = get_service(creds)
    processed_ids: set[str] = set()

    logger.info("Gmail Watcher running. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                count = poll_once(service, processed_ids)
                if count > 0:
                    logger.info(f"Ingested {count} new email(s)")
            except Exception as e:
                logger.error(f"Poll cycle error: {e}")

            time.sleep(GMAIL_POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Gmail Watcher stopped by user")


if __name__ == "__main__":
    main()
```

**New file: `.claude/skills/gmail-processor/SKILL.md`**
```markdown
# Gmail Processor Skill

## Purpose
Process email files ingested from Gmail. Analyze the email content,
determine urgency, extract action items, and categorize.

## Input
- Markdown file in /Needs_Action/ with `source: gmail` frontmatter
- Contains email headers, body text, and attachment references

## Processing Steps
1. Read the email markdown file
2. Analyze sender — is this a known contact or new?
3. Determine urgency based on:
   - Subject line keywords (urgent, asap, invoice, payment, deadline)
   - Sender importance (from Company_Handbook.md known contacts)
   - Content analysis
4. Extract action items (reply needed, payment required, meeting request)
5. If email has attachments, note them in action items
6. Categorize: client_email, invoice, newsletter, notification, personal, spam
7. Assign priority: high (client + action needed), medium (requires response), low (informational)
8. Write results to metadata file using inbox-processor output format
9. If action requires sending a reply or payment: flag for HITL approval

## Special Rules
- Never auto-reply to emails
- Flag any email mentioning money amounts > $500 as high priority
- Flag emails with attachments named "invoice" or "contract" as high priority
```

**Entry point addition to `pyproject.toml`:**
```toml
[project.scripts]
zoya-watcher = "src.watcher:main"
zoya-orchestrator = "src.orchestrator:main"
zoya-gmail = "src.gmail_watcher:main"
```

---

#### Task 2.4: Write Gmail Watcher Tests (1-2 hours)

**New file: `tests/test_gmail_watcher.py`**

Key tests:
```python
class TestExtractHeaders:
    def test_extracts_from_subject_date(self):
        """Headers parsed from Gmail message payload."""

    def test_missing_headers_returns_empty(self):
        """Gracefully handles messages without standard headers."""

class TestExtractBody:
    def test_simple_message_body(self):
        """Extracts body from non-multipart message."""

    def test_multipart_prefers_plain_text(self):
        """Selects text/plain over text/html in multipart."""

    def test_fallback_to_snippet(self):
        """Uses snippet when no body data available."""

class TestCreateEmailFile:
    def test_file_created_in_inbox(self, vault):
        """Email markdown file written to /Inbox/."""

    def test_frontmatter_includes_source_gmail(self, vault):
        """Frontmatter includes source: gmail."""

    def test_subject_sanitized_in_filename(self, vault):
        """Special characters removed from filename."""

class TestPollOnce:
    @patch("src.gmail_watcher.get_message_detail")
    @patch("src.gmail_watcher.fetch_unread_messages")
    def test_skips_already_processed(self, mock_fetch, mock_detail):
        """Messages in processed_ids set are skipped."""

    @patch("src.gmail_watcher.get_message_detail")
    @patch("src.gmail_watcher.fetch_unread_messages")
    def test_new_message_creates_file(self, mock_fetch, mock_detail, vault):
        """New unread message creates .md file in Inbox."""
```

**Verification:** All Gmail tests pass with `uv run pytest tests/test_gmail_watcher.py -v`

---

#### Phase 2 Dependencies
```
Task 2.1 (Google Cloud setup) must complete before Task 2.3
Task 2.2 (dependencies) must complete before Task 2.3
Task 2.3 (implementation) must complete before Task 2.4 (tests)
```

#### Phase 2 Success Criteria
- [ ] `credentials.json` exists and is gitignored
- [ ] First run opens browser, authenticates, saves `token.json`
- [ ] Gmail watcher polls for unread emails every 120 seconds
- [ ] New emails create `.md` files in `/Inbox/` with `source: gmail` frontmatter
- [ ] Attachments downloaded to `/Inbox/`
- [ ] Processed emails marked as read in Gmail
- [ ] Existing watcher + orchestrator pipeline processes the email files
- [ ] Gmail watcher tests pass
- [ ] All 69+ existing tests still pass

---

### Phase 3: HITL Approval Workflow (4-5 hours)

**Goal:** Implement a human-in-the-loop gate that routes sensitive actions to `/Pending_Approval/` and waits for human decision before proceeding.

#### Task 3.1: Define Approval Rules in Company_Handbook.md (30 min)

**Add to `AI_Employee_Vault/Company_Handbook.md`:**
```markdown
## Approval Rules (HITL)

Actions requiring human approval before execution:

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Invoice amount | > $500 | Route to /Pending_Approval/ |
| Contract deadline | < 7 days away | Route to /Pending_Approval/ |
| Outbound email | All | Route to /Pending_Approval/ |
| LinkedIn post | All | Route to /Pending_Approval/ |
| WhatsApp reply | All | Route to /Pending_Approval/ |
| File deletion | All | Route to /Pending_Approval/ |

Actions that auto-proceed (no approval needed):
- Document summarization
- Priority assignment
- Dashboard updates
- Plan.md creation
- Low-priority note processing
```

---

#### Task 3.2: Implement HITL Evaluator Skill (1 hour)

**New file: `.claude/skills/hitl-evaluator/SKILL.md`**
```markdown
# HITL Evaluator Skill

## Purpose
Determine whether a processed document requires human approval
before any further actions are taken.

## Input
- Processed metadata file (after inbox-processor has run)
- Company_Handbook.md approval rules

## Evaluation Logic
Read the processed metadata and check against approval rules:

1. Check document type and extracted fields:
   - type: invoice AND any mentioned amount > $500 → NEEDS APPROVAL
   - type: contract AND any deadline < 7 days from today → NEEDS APPROVAL
   - Any action item involving sending email/message → NEEDS APPROVAL
   - Any action item involving payment → NEEDS APPROVAL

2. If approval needed:
   - Set frontmatter: `approval_required: true`
   - Set frontmatter: `approval_reason: <reason>`
   - Do NOT move files (orchestrator handles movement)

3. If no approval needed:
   - Set frontmatter: `approval_required: false`
   - Processing continues normally

## Output Format (added to existing frontmatter)
approval_required: true
approval_reason: Invoice amount $2,500 exceeds $500 threshold
```

---

#### Task 3.3: Implement HITL in Orchestrator (2-3 hours)

**Changes to `src/orchestrator.py`:**

```python
from src.config import PENDING_APPROVAL, APPROVED, REJECTED, HITL_AMOUNT_THRESHOLD

def evaluate_hitl(meta_path: Path) -> bool:
    """Check if processed file needs human approval. Returns True if approval needed."""
    fm = _read_frontmatter(meta_path)

    # Check explicit flag set by Claude
    if fm.get("approval_required", "").lower() == "true":
        return True

    # Rule-based checks as fallback
    doc_type = fm.get("type", "other")
    priority = fm.get("priority", "low")
    source = fm.get("source", "file_drop")

    # Invoices are high-stakes
    if doc_type == "invoice" and priority == "high":
        return True

    # Contracts with approaching deadlines
    if doc_type == "contract" and priority == "high":
        return True

    # Any external-source document that might need reply
    if source in ("gmail", "whatsapp") and priority == "high":
        return True

    return False


def route_to_approval(meta_path: Path, companion: Path | None) -> Path:
    """Move file to /Pending_Approval/ for human review."""
    fm = _read_frontmatter(meta_path)
    reason = fm.get("approval_reason", "Matched HITL rule — manual review required")

    _update_frontmatter(meta_path, {
        "status": "pending_approval",
        "approval_reason": reason,
        "approval_requested_at": datetime.now().isoformat(),
    })

    # Move to Pending_Approval
    new_meta = PENDING_APPROVAL / meta_path.name
    meta_path.rename(new_meta)

    new_companion = None
    if companion and companion.exists():
        new_companion = PENDING_APPROVAL / companion.name
        companion.rename(new_companion)

    logger.info(f"Routed to approval: {new_meta.name} — {reason}")
    log_action("hitl_routed", str(new_meta), {"reason": reason}, "pending_approval")
    return new_meta


def process_approved_files():
    """Check /Approved/ for human-approved files and move to /Done/."""
    approved_files = sorted(APPROVED.glob("*.md"))
    for meta_path in approved_files:
        fm = _read_frontmatter(meta_path)
        if fm.get("status") in ("approved", "pending_approval"):
            _update_frontmatter(meta_path, {
                "status": "done",
                "approved_at": datetime.now().isoformat(),
                "approved_by": "human",
            })
            companion = _find_companion(meta_path, APPROVED)
            done_meta = DONE / meta_path.name
            meta_path.rename(done_meta)
            if companion:
                companion.rename(DONE / companion.name)

            logger.info(f"Approved and completed: {done_meta.name}")
            log_action("hitl_approved", str(done_meta), {}, "success")


def process_rejected_files():
    """Check /Rejected/ for human-rejected files and move to /Done/."""
    rejected_files = sorted(REJECTED.glob("*.md"))
    for meta_path in rejected_files:
        _update_frontmatter(meta_path, {
            "status": "rejected",
            "rejected_at": datetime.now().isoformat(),
            "rejected_by": "human",
        })
        companion = _find_companion(meta_path, REJECTED)
        done_meta = DONE / meta_path.name
        meta_path.rename(done_meta)
        if companion:
            companion.rename(DONE / companion.name)

        logger.info(f"Rejected: {done_meta.name}")
        log_action("hitl_rejected", str(done_meta), {}, "rejected")
```

**Modify `run_cycle()`:**
```python
def run_cycle() -> int:
    # Process approved/rejected files first
    process_approved_files()
    process_rejected_files()

    # Existing: poll Needs_Action, claim, process...
    # After Claude processes and before move_to_done:
    if evaluate_hitl(claimed_meta):
        route_to_approval(claimed_meta, claimed_companion)
        continue  # Don't move to Done yet

    move_to_done(claimed_meta, claimed_companion)
    # ...
```

**User workflow in Obsidian:**
1. Open Obsidian, see file appear in `/Pending_Approval/`
2. Review the document summary, action items, and approval reason
3. To approve: drag file from `/Pending_Approval/` to `/Approved/` in Obsidian file explorer
4. To reject: drag file to `/Rejected/`
5. Orchestrator picks it up on next cycle

---

#### Task 3.4: Write HITL Tests (1 hour)

**New file: `tests/test_hitl.py`**

```python
class TestEvaluateHitl:
    def test_invoice_high_priority_needs_approval(self, vault, sample_md):
        _update_frontmatter(sample_md, {"type": "invoice", "priority": "high"})
        assert evaluate_hitl(sample_md) is True

    def test_note_low_priority_no_approval(self, vault, sample_md):
        _update_frontmatter(sample_md, {"type": "note", "priority": "low"})
        assert evaluate_hitl(sample_md) is False

    def test_explicit_approval_flag(self, vault, sample_md):
        _update_frontmatter(sample_md, {"approval_required": "true"})
        assert evaluate_hitl(sample_md) is True

    def test_gmail_high_priority_needs_approval(self, vault, sample_md):
        _update_frontmatter(sample_md, {"source": "gmail", "priority": "high"})
        assert evaluate_hitl(sample_md) is True

class TestRouteToApproval:
    def test_file_moved_to_pending_approval(self, vault, sample_md):
        route_to_approval(sample_md, None)
        assert not sample_md.exists()
        assert (vault["PENDING_APPROVAL"] / sample_md.name).exists()

    def test_status_updated_to_pending_approval(self, vault, sample_md):
        new_path = route_to_approval(sample_md, None)
        fm = _read_frontmatter(new_path)
        assert fm["status"] == "pending_approval"

class TestProcessApprovedFiles:
    def test_approved_file_moved_to_done(self, vault):
        # Create a file in /Approved/
        approved = vault["APPROVED"] / "test.md"
        approved.write_text("---\nstatus: pending_approval\n---\nTest")
        process_approved_files()
        assert not approved.exists()
        assert (vault["DONE"] / "test.md").exists()

class TestProcessRejectedFiles:
    def test_rejected_file_moved_to_done_with_status(self, vault):
        rejected = vault["REJECTED"] / "test.md"
        rejected.write_text("---\nstatus: pending_approval\n---\nTest")
        process_rejected_files()
        fm = _read_frontmatter(vault["DONE"] / "test.md")
        assert fm["status"] == "rejected"
```

---

#### Phase 3 Dependencies
```
Phase 1 must be complete (new vault folders exist)
Plan.md skill helps HITL evaluator understand document context
```

#### Phase 3 Success Criteria
- [ ] High-priority invoices and contracts route to `/Pending_Approval/`
- [ ] Low-priority notes flow directly to `/Done/` (no approval needed)
- [ ] Files moved to `/Approved/` by user are processed to `/Done/`
- [ ] Files moved to `/Rejected/` are archived to `/Done/` with `status: rejected`
- [ ] Approval reason logged in frontmatter and JSON audit log
- [ ] Existing Bronze pipeline unaffected for documents not needing approval
- [ ] HITL tests pass
- [ ] All existing tests still pass

---

### Phase 4: MCP Server (4-5 hours)

**Goal:** Build one working MCP server for email operations that Claude Code can invoke as a tool.

#### Task 4.1: Choose MCP Approach (30 min decision)

| Approach | Effort | Reliability | Recommendation |
|----------|--------|-------------|----------------|
| Build custom Python MCP server | 4-5h | Medium | Full control, more code |
| Use `@anthropic/mcp-server` Node.js template | 3-4h | High | Good docs, standard approach |
| Use existing community MCP server | 1-2h | Varies | Fastest, but less custom |

**Recommendation:** Build a Python-based MCP server using the `mcp` Python SDK. This keeps the entire stack in Python (consistent with the project) and gives full control.

```bash
uv add mcp
```

---

#### Task 4.2: Implement Email MCP Server (3-4 hours)

**New file: `src/mcp/email_server.py`**

```python
"""Email MCP Server - provides email tools to Claude Code.

Tools:
  - send_email: Draft/send an email via Gmail API
  - search_emails: Search inbox by query
  - list_recent_emails: List N most recent emails

All send operations return a "pending_approval" status rather than
actually sending — the HITL workflow handles final send.
"""

import json
import base64
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText

from mcp.server import Server
from mcp.types import Tool, TextContent

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths - relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"
GMAIL_TOKEN = PROJECT_ROOT / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

app = Server("email-mcp")


def _get_gmail_service():
    """Build authenticated Gmail service."""
    if not GMAIL_TOKEN.exists():
        raise RuntimeError("Gmail not authenticated. Run gmail_watcher first.")
    creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), SCOPES)
    return build("gmail", "v1", credentials=creds)


@app.tool()
async def send_email(to: str, subject: str, body: str) -> str:
    """Draft an email and route it through HITL approval.

    Does NOT send immediately. Creates an approval request file
    in /Pending_Approval/. The email is sent only after human approval.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body text
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_subject = "".join(c if c.isalnum() or c in "_-" else "_" for c in subject)[:40]

    approval_file = PENDING_APPROVAL / f"SEND_EMAIL_{timestamp}_{safe_subject}.md"
    approval_file.write_text(f"""---
type: email_send
action: send_email
status: pending_approval
to: {to}
subject: {subject}
created: {datetime.now().isoformat()}
source: mcp_email_server
approval_required: true
approval_reason: Outbound email requires human approval
---

## Email Draft

**To:** {to}
**Subject:** {subject}

{body}

---

## To Approve
Move this file to /Approved/ in Obsidian.

## To Reject
Move this file to /Rejected/ in Obsidian.
""")
    return f"Email draft created and routed for approval: {approval_file.name}"


@app.tool()
async def search_emails(query: str, max_results: int = 5) -> str:
    """Search Gmail inbox and return matching emails.

    Args:
        query: Gmail search query (e.g., 'from:client@example.com subject:invoice')
        max_results: Maximum number of results to return (default: 5)
    """
    service = _get_gmail_service()
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return "No emails found matching query."

    output_lines = [f"Found {len(messages)} email(s):\n"]
    for msg_summary in messages[:max_results]:
        msg = service.users().messages().get(
            userId="me", id=msg_summary["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        output_lines.append(
            f"- **{headers.get('Subject', 'No Subject')}** "
            f"from {headers.get('From', 'Unknown')} "
            f"({headers.get('Date', 'Unknown date')})"
        )

    return "\n".join(output_lines)


@app.tool()
async def list_recent_emails(count: int = 10) -> str:
    """List the N most recent emails in the inbox.

    Args:
        count: Number of recent emails to list (default: 10)
    """
    return await search_emails(query="in:inbox", max_results=count)


def main():
    """Run the MCP server."""
    import asyncio
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
```

---

#### Task 4.3: Configure MCP in Claude Code (30 min)

**New file: `.claude/mcp.json`**
```json
{
  "servers": {
    "email": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp.email_server"],
      "cwd": "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"
    }
  }
}
```

**Verify MCP connection:**
```bash
claude mcp list   # Should show "email" server
```

---

#### Task 4.4: Write MCP Tests (1 hour)

Test the tool functions directly (mock Gmail API):

```python
# tests/test_mcp_email.py

class TestSendEmail:
    def test_creates_approval_file(self, vault):
        """send_email creates file in /Pending_Approval/."""
        import asyncio
        result = asyncio.run(send_email("test@example.com", "Test", "Hello"))
        files = list(vault["PENDING_APPROVAL"].glob("SEND_EMAIL_*.md"))
        assert len(files) == 1
        assert "test@example.com" in files[0].read_text()

    def test_does_not_actually_send(self, vault):
        """send_email never calls Gmail send API directly."""
        # No Gmail API mock needed — function doesn't call it

class TestSearchEmails:
    @patch("src.mcp.email_server._get_gmail_service")
    def test_returns_formatted_results(self, mock_service):
        """Search results formatted as markdown list."""

    @patch("src.mcp.email_server._get_gmail_service")
    def test_empty_results(self, mock_service):
        """Returns helpful message when no results found."""
```

---

#### Phase 4 Dependencies
```
Phase 2 (Gmail setup) must be complete — MCP reuses Gmail credentials
Phase 3 (HITL) must be complete — send_email routes through approval
```

#### Phase 4 Success Criteria
- [ ] MCP server starts without errors
- [ ] `claude mcp list` shows "email" server
- [ ] `send_email` tool creates approval file in `/Pending_Approval/`
- [ ] `search_emails` returns formatted Gmail results
- [ ] No email ever sent without going through HITL first
- [ ] MCP tests pass

---

### Phase 5: LinkedIn + Extra Watcher (5-7 hours)

**Goal:** Implement LinkedIn auto-posting (S3) and a second watcher (S2). The combination of Gmail watcher + either WhatsApp or LinkedIn satisfies the "two or more watchers" requirement.

#### Task 5.1: LinkedIn API Access (1 hour setup + wait time)

**Option A: LinkedIn API (Recommended for production)**

1. Go to https://www.linkedin.com/developers/apps
2. Create a new app
3. Request `w_member_social` scope (for posting)
4. Get Client ID and Client Secret
5. Generate an access token via OAuth2 flow

**Option B: Playwright Browser Automation (Fallback)**

If LinkedIn API access is delayed, use Playwright to automate posting via the web interface.

```bash
uv add playwright
uv run playwright install chromium
```

**Option C: Hybrid approach (recommended for hackathon)**

Generate content with Claude, create approval file, then post via whichever method is available.

---

#### Task 5.2: Implement LinkedIn Poster (3-4 hours)

**New file: `src/linkedin_poster.py`**

```python
"""LinkedIn Auto-Poster — generates and posts business content.

Flow:
1. Claude generates post content based on business context
2. Post goes to /Pending_Approval/ (HITL — never auto-post)
3. On approval, post is published via LinkedIn API or Playwright
4. Result logged to /Done/

Can be triggered by:
- Cron job (weekly posting schedule)
- Manual invocation
- Orchestrator (when a task suggests social media action)
"""

import subprocess
import time
from datetime import datetime
from pathlib import Path

from src.config import (
    PROJECT_ROOT, VAULT_PATH, PENDING_APPROVAL, APPROVED, DONE,
    LINKEDIN_DRY_RUN,
)
from src.utils import setup_logger, log_action

logger = setup_logger("linkedin_poster")


def generate_post_content() -> str | None:
    """Use Claude to generate a LinkedIn post based on business context.

    Reads Dashboard.md, Company_Handbook.md, and recent activity
    to craft a relevant business post.
    """
    prompt = (
        "You are Zoya. Use the linkedin-poster skill.\n\n"
        "Generate a LinkedIn post for the business. Read:\n"
        f"- `{VAULT_PATH / 'Dashboard.md'}` for recent activity\n"
        f"- `{VAULT_PATH / 'Company_Handbook.md'}` for business context\n\n"
        "Write a professional LinkedIn post (150-300 words) that:\n"
        "- Highlights recent business achievements or insights\n"
        "- Provides value to the audience\n"
        "- Includes a call to action\n"
        "- Uses a professional but approachable tone\n"
        "- Does NOT use excessive hashtags (max 3)\n\n"
        "Output ONLY the post text, nothing else.\n"
    )

    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions", prompt],
        capture_output=True, text=True, timeout=60, cwd=str(PROJECT_ROOT),
    )

    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    logger.error(f"Content generation failed: {result.stderr[:200]}")
    return None


def create_approval_request(content: str) -> Path:
    """Create an approval file for the LinkedIn post."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = PENDING_APPROVAL / f"LINKEDIN_POST_{timestamp}.md"

    filepath.write_text(f"""---
type: linkedin_post
action: post_to_linkedin
status: pending_approval
created: {datetime.now().isoformat()}
source: linkedin_poster
approval_required: true
approval_reason: All social media posts require human review before publishing
platform: linkedin
---

## LinkedIn Post Draft

{content}

---

## Instructions
- Review the post content above
- Edit the content section if needed (changes will be reflected in the final post)
- **To Approve:** Move this file to /Approved/
- **To Reject:** Move this file to /Rejected/
""")

    logger.info(f"LinkedIn post approval request created: {filepath.name}")
    log_action("linkedin_draft", str(filepath), {"platform": "linkedin"}, "pending_approval")
    return filepath


def post_to_linkedin(content: str) -> bool:
    """Publish content to LinkedIn.

    Uses LinkedIn API if available, falls back to dry-run logging.
    """
    if LINKEDIN_DRY_RUN:
        logger.info(f"[DRY RUN] Would post to LinkedIn: {content[:80]}...")
        log_action("linkedin_post", "dry_run", {"content_preview": content[:100]}, "dry_run")
        return True

    # LinkedIn API implementation
    # This will be filled in when API access is granted
    logger.warning("LinkedIn API posting not yet implemented. Using dry-run mode.")
    return False


def process_approved_posts():
    """Check /Approved/ for LinkedIn posts and publish them."""
    from src.orchestrator import _read_frontmatter

    for filepath in sorted(APPROVED.glob("LINKEDIN_POST_*.md")):
        fm = _read_frontmatter(filepath)
        if fm.get("type") != "linkedin_post":
            continue

        # Extract post content (everything between "## LinkedIn Post Draft" and "---")
        text = filepath.read_text()
        start = text.find("## LinkedIn Post Draft")
        end = text.find("---", start + 10) if start != -1 else -1

        if start != -1 and end != -1:
            content = text[start + len("## LinkedIn Post Draft"):end].strip()
            success = post_to_linkedin(content)

            status = "posted" if success else "post_failed"
            from src.orchestrator import _update_frontmatter
            _update_frontmatter(filepath, {
                "status": status,
                "posted_at": datetime.now().isoformat(),
            })

            done_path = DONE / filepath.name
            filepath.rename(done_path)
            logger.info(f"LinkedIn post {status}: {done_path.name}")


def main():
    """Generate a LinkedIn post and route for approval."""
    logger.info("LinkedIn Poster starting")

    content = generate_post_content()
    if content:
        create_approval_request(content)
        logger.info("Post generated and sent for approval")
    else:
        logger.error("Failed to generate post content")


if __name__ == "__main__":
    main()
```

**New file: `.claude/skills/linkedin-poster/SKILL.md`**
```markdown
# LinkedIn Poster Skill

## Purpose
Generate professional LinkedIn posts based on recent business activity
and context from the vault. Posts are always routed through HITL approval.

## Input
- Dashboard.md (recent activity, metrics)
- Company_Handbook.md (business context, tone guidelines)
- Optional: specific topic or event to highlight

## Output
A LinkedIn post (150-300 words) that:
- Is professional but approachable
- Highlights a recent achievement, insight, or value proposition
- Includes a clear call to action
- Uses max 3 relevant hashtags
- Does NOT mention AI/automation (unless the business is about AI)
- Does NOT include links unless specifically requested

## Post Types (rotate between these)
1. **Achievement post** — milestone, client win, project completion
2. **Insight post** — industry observation, lesson learned
3. **Value post** — tip, guide, how-to for the audience
4. **Behind-the-scenes** — process, workflow, team culture

## Rules
- NEVER auto-post. Always create an approval file.
- Keep tone consistent with Company_Handbook.md guidelines
- Output ONLY the post text, no explanation or formatting instructions
```

---

#### Task 5.3: Implement WhatsApp Watcher (2-3 hours)

**Approach: Twilio WhatsApp Sandbox** (most hackathon-friendly)

```bash
uv add flask twilio
```

**New file: `src/whatsapp_watcher.py`**

```python
"""WhatsApp Watcher — receives messages via Twilio webhook.

Setup:
1. Create Twilio account at twilio.com
2. Activate WhatsApp Sandbox (Messaging > Try WhatsApp)
3. Set webhook URL to: http://<your-ngrok-url>/whatsapp
4. Run: ngrok http 5001

Environment variables needed (.env):
  TWILIO_ACCOUNT_SID=your_sid
  TWILIO_AUTH_TOKEN=your_token
"""

import os
from datetime import datetime
from pathlib import Path

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from src.config import INBOX, PROJECT_ROOT
from src.utils import setup_logger, log_action

logger = setup_logger("whatsapp_watcher")

app = Flask(__name__)

WEBHOOK_PORT = int(os.getenv("WHATSAPP_PORT", "5001"))


def create_message_file(from_number: str, body: str, media_url: str | None = None) -> Path:
    """Create a markdown file in /Inbox/ for an incoming WhatsApp message."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_from = "".join(c if c.isalnum() else "_" for c in from_number)[-10:]

    filepath = INBOX / f"WHATSAPP_{timestamp}_{safe_from}.md"

    media_section = ""
    if media_url:
        media_section = f"\n## Media\n- Attachment: {media_url}\n"

    filepath.write_text(f"""---
type: whatsapp_message
source: whatsapp
from: {from_number}
received: {datetime.now().isoformat()}
status: pending
priority: medium
---

## WhatsApp Message

**From:** {from_number}
**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{body}
{media_section}
## Suggested Actions
- [ ] Review message content
- [ ] Reply to sender (requires approval)
""")

    logger.info(f"WhatsApp message saved: {filepath.name}")
    log_action("whatsapp_ingested", str(filepath), {"from": from_number}, "success")
    return filepath


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages from Twilio."""
    from_number = request.values.get("From", "Unknown")
    body = request.values.get("Body", "")
    media_url = request.values.get("MediaUrl0")
    num_media = int(request.values.get("NumMedia", 0))

    logger.info(f"WhatsApp message from {from_number}: {body[:50]}...")

    create_message_file(from_number, body, media_url if num_media > 0 else None)

    # Acknowledge receipt (optional auto-reply)
    resp = MessagingResponse()
    # Uncomment to auto-acknowledge:
    # resp.message("Received. Zoya is processing your message.")
    return str(resp)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "whatsapp_watcher"}


def main():
    """Start the WhatsApp webhook server."""
    logger.info(f"WhatsApp Watcher starting on port {WEBHOOK_PORT}")
    logger.info("Ensure ngrok is running: ngrok http {WEBHOOK_PORT}")
    app.run(host="0.0.0.0", port=WEBHOOK_PORT, debug=False)


if __name__ == "__main__":
    main()
```

**New file: `.claude/skills/whatsapp-processor/SKILL.md`**
```markdown
# WhatsApp Processor Skill

## Purpose
Process WhatsApp messages ingested from Twilio webhook.
Analyze message content, determine urgency, extract action items.

## Input
- Markdown file in /Needs_Action/ with `source: whatsapp` frontmatter
- Contains sender number, message body, optional media reference

## Processing Steps
1. Read the WhatsApp message markdown file
2. Analyze message content for:
   - Keywords: urgent, asap, invoice, payment, help, deadline
   - Sentiment: positive, negative, neutral
   - Intent: request, question, update, complaint
3. Extract action items (reply needed, follow-up task)
4. Categorize: client_message, support_request, personal, spam
5. Assign priority:
   - high: contains urgency keywords or payment references
   - medium: requires response
   - low: informational
6. Write results to metadata file

## Special Rules
- NEVER auto-reply to WhatsApp messages
- All replies must go through HITL approval
- Flag messages mentioning money or deadlines as high priority
```

---

#### Phase 5 Dependencies
```
Phase 3 (HITL) must be complete — LinkedIn posts and WhatsApp replies route through approval
Gmail watcher (Phase 2) should be working — validates the watcher pattern
```

#### Phase 5 Success Criteria
- [ ] LinkedIn poster generates content via Claude
- [ ] Post drafts appear in `/Pending_Approval/` for review
- [ ] Approved posts are logged (dry-run mode counts for demo)
- [ ] WhatsApp webhook receives messages from Twilio
- [ ] WhatsApp messages create `.md` files in `/Inbox/` with `source: whatsapp`
- [ ] Existing pipeline processes WhatsApp message files
- [ ] LinkedIn poster + WhatsApp tests pass
- [ ] 2+ watchers requirement met (file system + Gmail + WhatsApp/LinkedIn)

---

### Phase 6: Scheduling & Polish (2-3 hours)

**Goal:** Set up cron-based scheduling (S7), ensure all features work end-to-end, and verify all Agent Skills are complete (S8).

#### Task 6.1: Implement Scheduling (1 hour)

**Approach comparison:**

| Scheduler | Pros | Cons | Verdict |
|-----------|------|------|---------|
| cron (Linux native) | Zero deps, battle-tested, survives reboots | No logging UI, unfriendly syntax | **Use this** |
| systemd timers | More features than cron, journald logging | More complex setup | Overkill for hackathon |
| PM2 | Process management + scheduling, web UI | Node.js dependency | Good for prod |
| Python `schedule` lib | Pure Python, readable syntax | Needs its own process running | Extra process to manage |

**Cron setup:**

```bash
# Open crontab editor
crontab -e

# Add these entries:

# ┌─── Daily dashboard refresh at 8:00 AM
0 8 * * * cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE" && /usr/bin/env uv run python -m src.orchestrator --once >> AI_Employee_Vault/Logs/cron.log 2>&1

# ┌─── Weekly LinkedIn post generation on Monday 9:00 AM
0 9 * * 1 cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE" && /usr/bin/env uv run python -m src.linkedin_poster >> AI_Employee_Vault/Logs/cron.log 2>&1

# ┌─── Weekly briefing generation on Monday 8:00 AM
0 8 * * 1 cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE" && /usr/bin/env claude --print --dangerously-skip-permissions "Use the scheduled-briefing skill. Generate a weekly briefing for Zoya based on AI_Employee_Vault/Dashboard.md and recent activity in AI_Employee_Vault/Done/. Write the briefing to AI_Employee_Vault/Briefings/$(date +\%Y-\%m-\%d)_weekly.md" >> AI_Employee_Vault/Logs/cron.log 2>&1
```

**New file: `.claude/skills/scheduled-briefing/SKILL.md`**
```markdown
# Scheduled Briefing Skill

## Purpose
Generate periodic briefings summarizing recent AI Employee activity.
Triggered by cron on a schedule (weekly by default).

## Input
- Dashboard.md (current system state)
- Recent files in /Done/ (last 7 days of activity)
- Company_Handbook.md (business context)

## Output
Write a briefing to: AI_Employee_Vault/Briefings/<date>_weekly.md

## Briefing Format
---
generated: <ISO timestamp>
period: <start_date> to <end_date>
type: weekly_briefing
---

# Weekly Briefing — <date range>

## Summary
<2-3 sentence overview of the week>

## Activity
- Files processed: <count>
- Emails ingested: <count>
- Items approved: <count>
- Items rejected: <count>
- Items quarantined: <count>

## Highlights
- <Notable items processed this week>

## Pending Items
- <Items still in Pending_Approval>
- <Items in Needs_Action>

## Recommendations
- <Suggestions based on patterns observed>
```

**New file: `scripts/start_silver.sh`**
```bash
#!/usr/bin/env bash
# start_silver.sh — Launch all Silver tier processes
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Starting Zoya Silver Tier..."
echo "Project: $PROJECT_DIR"
echo ""

# Start file watcher
echo "[1/3] Starting File System Watcher..."
uv run python -m src.watcher &
WATCHER_PID=$!
echo "  PID: $WATCHER_PID"

# Start Gmail watcher
echo "[2/3] Starting Gmail Watcher..."
uv run python -m src.gmail_watcher &
GMAIL_PID=$!
echo "  PID: $GMAIL_PID"

# Start orchestrator
echo "[3/3] Starting Orchestrator..."
uv run python -m src.orchestrator &
ORCH_PID=$!
echo "  PID: $ORCH_PID"

echo ""
echo "All processes running. Press Ctrl+C to stop all."
echo "PIDs: watcher=$WATCHER_PID gmail=$GMAIL_PID orchestrator=$ORCH_PID"

# Trap Ctrl+C to kill all children
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $WATCHER_PID $GMAIL_PID $ORCH_PID 2>/dev/null
    wait
    echo "All processes stopped."
}
trap cleanup INT TERM

wait
```

```bash
chmod +x scripts/start_silver.sh
```

---

#### Task 6.2: Verify All Agent Skills — S8 (30 min)

**Complete skills inventory for Silver:**

| # | Skill | Directory | Status |
|---|-------|-----------|--------|
| 1 | inbox-processor | `.claude/skills/inbox-processor/` | EXISTING (Bronze) |
| 2 | dashboard-updater | `.claude/skills/dashboard-updater/` | EXISTING (Bronze) |
| 3 | vault-init | `.claude/skills/vault-init/` | EXISTING (Bronze) |
| 4 | plan-creator | `.claude/skills/plan-creator/` | NEW (Phase 1) |
| 5 | hitl-evaluator | `.claude/skills/hitl-evaluator/` | NEW (Phase 3) |
| 6 | gmail-processor | `.claude/skills/gmail-processor/` | NEW (Phase 2) |
| 7 | whatsapp-processor | `.claude/skills/whatsapp-processor/` | NEW (Phase 5) |
| 8 | linkedin-poster | `.claude/skills/linkedin-poster/` | NEW (Phase 5) |
| 9 | scheduled-briefing | `.claude/skills/scheduled-briefing/` | NEW (Phase 6) |

**Verification:** `ls .claude/skills/` shows 9 directories, each with SKILL.md.

---

#### Task 6.3: Update .gitignore (15 min)

**Add to `.gitignore`:**
```
# Silver tier additions
AI_Employee_Vault/Plans/*
AI_Employee_Vault/Pending_Approval/*
AI_Employee_Vault/Approved/*
AI_Employee_Vault/Rejected/*
AI_Employee_Vault/Briefings/*
!AI_Employee_Vault/*/.gitkeep
```

---

#### Task 6.4: Update pyproject.toml Scripts (15 min)

```toml
[project.scripts]
zoya-watcher = "src.watcher:main"
zoya-orchestrator = "src.orchestrator:main"
zoya-gmail = "src.gmail_watcher:main"
zoya-whatsapp = "src.whatsapp_watcher:main"
zoya-linkedin = "src.linkedin_poster:main"
```

---

#### Phase 6 Dependencies
```
All previous phases complete.
This phase is integration + polish.
```

#### Phase 6 Success Criteria
- [ ] Cron jobs installed and verified (`crontab -l` shows entries)
- [ ] `--once` mode orchestrator runs and exits cleanly
- [ ] Weekly briefing generates to `/Briefings/`
- [ ] All 9 Agent Skills have SKILL.md files
- [ ] `scripts/start_silver.sh` launches all processes
- [ ] `.gitignore` covers all new vault folders
- [ ] pyproject.toml has all entry points

---

## 4. Technical Specifications

### 4.1 Gmail Watcher

| Aspect | Detail |
|--------|--------|
| **Packages** | `google-api-python-client>=2.100.0`, `google-auth-oauthlib>=1.2.0`, `google-auth-httplib2>=0.2.0` |
| **Auth flow** | OAuth2 Desktop App → browser consent → `token.json` stored locally |
| **Polling** | Every 120 seconds (configurable via `GMAIL_POLL_INTERVAL`) |
| **Filters** | `is:unread` in `INBOX` label |
| **Dedup** | `processed_ids` set (in-memory per session) + Gmail marks as read |
| **Attachments** | Downloaded to `/Inbox/` with `GMAIL_` prefix |
| **Error handling** | Per-message try/catch; one failure doesn't stop polling |
| **Token refresh** | Automatic via `google-auth` library (refresh token stored) |
| **Rate limit** | Gmail API: 250 quota units/sec, 1B/day (well within limits for polling) |

### 4.2 WhatsApp Watcher

| Aspect | Detail |
|--------|--------|
| **Recommended API** | Twilio WhatsApp Sandbox (free tier, reliable, good docs) |
| **Architecture** | Webhook (Flask server on port 5001) + ngrok for public URL |
| **Message parsing** | Twilio provides structured form data: `From`, `Body`, `MediaUrl0` |
| **Media** | URL reference stored in metadata (download optional) |
| **Cost** | Twilio free tier: ~500 messages. Paid: $0.005/message |
| **Alternative** | Playwright automation of WhatsApp Web (fragile, not recommended) |

### 4.3 LinkedIn Automation

| Aspect | Detail |
|--------|--------|
| **API option** | LinkedIn Marketing API with `w_member_social` scope |
| **API risk** | Requires app review — may take days. Apply early. |
| **Fallback** | Content generation + dry-run logging (demonstrates the flow) |
| **Content strategy** | Claude generates 150-300 word posts based on business context |
| **Frequency** | Weekly (Monday 9 AM via cron) |
| **Safety** | ALL posts go through HITL — never auto-post |
| **Compliance** | LinkedIn ToS allows API posting. Web scraping is against ToS. |

### 4.4 MCP Server

| Aspect | Detail |
|--------|--------|
| **Server type** | Python MCP server using `mcp` SDK |
| **Tools** | `send_email`, `search_emails`, `list_recent_emails` |
| **Config** | `.claude/mcp.json` — registered as "email" server |
| **Invocation** | Claude Code calls tools automatically when relevant |
| **Safety** | `send_email` creates approval file, never sends directly |
| **Testing** | Mock Gmail API; test tool functions directly |

### 4.5 HITL Workflow

| Aspect | Detail |
|--------|--------|
| **Approval file format** | Markdown with YAML frontmatter (`status: pending_approval`) |
| **Folder structure** | `/Pending_Approval/` → user moves to `/Approved/` or `/Rejected/` |
| **Notification** | User checks Obsidian (future: desktop notification via `notify-send`) |
| **Thresholds** | Invoices >$500, contracts <7 days, all outbound emails/posts |
| **Polling** | Orchestrator checks `/Approved/` and `/Rejected/` every cycle |
| **Audit** | Every approval/rejection logged to JSON audit log |

### 4.6 Scheduling

| Aspect | Detail |
|--------|--------|
| **Recommended** | cron (Linux native, zero dependencies, survives reboots) |
| **Entries** | Daily dashboard refresh, weekly LinkedIn post, weekly briefing |
| **Orchestrator flag** | `--once` runs single cycle and exits (for cron use) |
| **Logging** | Cron output appended to `AI_Employee_Vault/Logs/cron.log` |
| **Persistence** | Cron entries survive reboots by default |

---

## 5. Risk Analysis & Mitigation

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | **LinkedIn API access delayed** | High | High | Apply immediately. Fallback: dry-run + content generation demo |
| 2 | **Gmail OAuth rejected** | Low | High | Use "Desktop app" type + add self as test user |
| 3 | **Token expiry during demo** | Medium | High | Test refresh flow; re-authenticate 1 day before demo |
| 4 | **WhatsApp Playwright breaks** | High | Medium | Use Twilio sandbox instead (recommended) |
| 5 | **Twilio webhook unreachable** | Medium | Medium | Use ngrok; test webhook with curl before demo |
| 6 | **MCP protocol errors** | Medium | Medium | Use official `mcp` Python SDK; follow examples exactly |
| 7 | **HITL breaks existing pipeline** | Medium | High | Extensive tests; HITL is opt-in (only for flagged items) |
| 8 | **Plan.md adds latency** | Low | Low | Plan creation is non-blocking; failure falls through to normal processing |
| 9 | **Rate limits hit** | Low | Medium | Gmail: 250/sec (fine). LinkedIn: test post count. Twilio: monitor usage |
| 10 | **Credential leak** | Low | Critical | .gitignore verified; pre-commit hook recommended |

### API Rate Limits

| Service | Free Tier Limit | Our Usage Pattern | Risk |
|---------|----------------|-------------------|------|
| Gmail API | 1B quota units/day | ~50 calls/hour (polling + reads) | Negligible |
| LinkedIn API | 100 posts/day | 1 post/week | Negligible |
| Twilio WhatsApp | 500 messages (trial) | Inbound only | Low |
| Claude Code | Per-subscription | ~20-50 invocations/day | Monitor costs |

### Authentication Token Lifecycle

```
Gmail OAuth2:
  credentials.json (permanent) → first auth → token.json (auto-refreshes)
  Risk: refresh token can expire after 7 days if app is in "testing" mode
  Fix: Publish OAuth consent screen OR re-auth before demo

LinkedIn OAuth2:
  Client ID + Secret → access token (60 days)
  Risk: Token expires, no auto-refresh
  Fix: Re-generate token before demo

Twilio:
  Account SID + Auth Token (permanent until rotated)
  Risk: None (doesn't expire)
```

---

## 6. Testing Strategy

### 6.1 Test Coverage Target

| Component | Test File | Tests (est.) | Priority |
|-----------|-----------|-------------|----------|
| Config (Silver paths) | `test_config.py` | +5 | High |
| Plan creator | `test_plan_creator.py` | 6-8 | High |
| HITL workflow | `test_hitl.py` | 10-12 | Critical |
| Gmail watcher | `test_gmail_watcher.py` | 10-12 | High |
| WhatsApp watcher | `test_whatsapp_watcher.py` | 6-8 | Medium |
| LinkedIn poster | `test_linkedin_poster.py` | 6-8 | Medium |
| MCP email server | `test_mcp_email.py` | 6-8 | High |
| Scheduler/--once | `test_scheduler.py` | 3-4 | Medium |
| **Total new tests** | | **47-60** | |
| **Total (Bronze + Silver)** | | **116-129** | |

### 6.2 Integration Test Scenarios

```
Scenario 1: Gmail → Pipeline → Done
  1. Mock Gmail API returns unread email
  2. gmail_watcher creates EMAIL_*.md in /Inbox/
  3. watcher.py detects file, creates metadata in /Needs_Action/
  4. orchestrator claims, processes with Claude (mocked)
  5. File ends up in /Done/ with summary

Scenario 2: Email → HITL → Approval → Done
  1. Mock email with invoice > $500
  2. Pipeline processes and flags for approval
  3. File appears in /Pending_Approval/
  4. Simulate user moving to /Approved/
  5. Orchestrator picks up, moves to /Done/ with approved_by: human

Scenario 3: LinkedIn → Approval → Post
  1. LinkedIn poster generates content (Claude mocked)
  2. Approval file created in /Pending_Approval/
  3. Simulate user approval
  4. Dry-run post logged

Scenario 4: Cron --once mode
  1. Start orchestrator with --once
  2. Process pending items
  3. Verify orchestrator exits (doesn't loop)
```

### 6.3 Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run only Silver tests
uv run pytest tests/test_gmail_watcher.py tests/test_hitl.py tests/test_plan_creator.py tests/test_linkedin_poster.py tests/test_whatsapp_watcher.py tests/test_mcp_email.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### 6.4 Silver Tier Verification Checklist

```bash
# S1: Bronze still works
uv run pytest tests/test_config.py tests/test_utils.py tests/test_watcher.py tests/test_orchestrator.py -v

# S2: Two+ watchers
ls src/gmail_watcher.py src/whatsapp_watcher.py   # Both exist
uv run python -m src.gmail_watcher --help          # Starts without error

# S3: LinkedIn posting
uv run python -m src.linkedin_poster               # Creates approval file

# S4: Plan.md
# Drop an invoice in /Inbox/, check /Plans/ for Plan.md

# S5: MCP server
claude mcp list                                    # Shows "email" server

# S6: HITL
# Check /Pending_Approval/ has files needing review

# S7: Scheduling
crontab -l                                         # Shows cron entries

# S8: All skills
ls .claude/skills/                                 # Shows 9 directories
```

---

## 7. File Structure Changes

Complete tree of files ADDED or MODIFIED for Silver:

```
PIA-CLAUDE/
│
├── [MODIFIED] pyproject.toml           # +4 dependencies, +3 entry points
├── [MODIFIED] .gitignore               # +5 vault folder exclusions
├── [NEW]      Silver_Tier_Blueprint.md # This file
│
├── src/
│   ├── [MODIFIED] config.py            # +5 paths, +4 settings constants
│   ├── [MODIFIED] orchestrator.py      # +plan_creator, +hitl, +--once flag
│   ├── [NEW]      gmail_watcher.py     # ~200 lines
│   ├── [NEW]      whatsapp_watcher.py  # ~120 lines
│   ├── [NEW]      linkedin_poster.py   # ~150 lines
│   ├── [NEW]      scheduler.py         # ~50 lines (optional helper)
│   └── mcp/
│       ├── [NEW]  __init__.py
│       └── [NEW]  email_server.py      # ~150 lines
│
├── .claude/
│   ├── [MODIFIED] settings.local.json  # +new permissions
│   ├── [NEW]      mcp.json             # MCP server config
│   └── skills/
│       ├── [NEW]  plan-creator/SKILL.md
│       ├── [NEW]  hitl-evaluator/SKILL.md
│       ├── [NEW]  gmail-processor/SKILL.md
│       ├── [NEW]  whatsapp-processor/SKILL.md
│       ├── [NEW]  linkedin-poster/SKILL.md
│       └── [NEW]  scheduled-briefing/SKILL.md
│
├── AI_Employee_Vault/
│   ├── [MODIFIED] Company_Handbook.md  # +HITL approval rules
│   ├── [NEW]      Plans/.gitkeep
│   ├── [NEW]      Pending_Approval/.gitkeep
│   ├── [NEW]      Approved/.gitkeep
│   ├── [NEW]      Rejected/.gitkeep
│   └── [NEW]      Briefings/.gitkeep
│
├── tests/
│   ├── [MODIFIED] conftest.py          # +new fixtures (gmail, hitl, linkedin)
│   ├── [MODIFIED] test_config.py       # +tests for new paths
│   ├── [NEW]      test_gmail_watcher.py
│   ├── [NEW]      test_whatsapp_watcher.py
│   ├── [NEW]      test_linkedin_poster.py
│   ├── [NEW]      test_hitl.py
│   ├── [NEW]      test_plan_creator.py
│   └── [NEW]      test_mcp_email.py
│
└── scripts/
    └── [NEW]      start_silver.sh      # Launch all processes
```

**Lines of code estimate:**
- New source files: ~670 lines
- Modified source files: ~100 lines added
- New test files: ~400 lines
- New skill files: ~200 lines
- **Total new code: ~1,370 lines**

---

## 8. Quick Start Checklist

| # | Task | Est. Time | Command / Action |
|---|------|-----------|------------------|
| 1 | Apply for LinkedIn API access | 10 min | https://www.linkedin.com/developers/apps — do this NOW (approval takes days) |
| 2 | Create new vault folders | 5 min | `mkdir -p AI_Employee_Vault/{Plans,Pending_Approval,Approved,Rejected,Briefings}` |
| 3 | Add Silver paths to `config.py` | 15 min | Add `PLANS`, `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `BRIEFINGS` constants |
| 4 | Implement Plan.md skill + orchestrator changes | 2 hours | Create `plan-creator/SKILL.md`, add `should_create_plan()` + `create_plan()` to orchestrator |
| 5 | Add `--once` flag to orchestrator | 20 min | Add `argparse` with `--once` argument to `main()` |
| 6 | Set up Google Cloud + Gmail API credentials | 1 hour | https://console.cloud.google.com — create project, enable API, download `credentials.json` |
| 7 | Install Gmail dependencies | 5 min | `uv add google-api-python-client google-auth-oauthlib google-auth-httplib2` |
| 8 | Implement Gmail watcher | 3 hours | Create `src/gmail_watcher.py` with OAuth, polling, email parsing |
| 9 | Implement HITL approval workflow | 3 hours | Add `evaluate_hitl()`, `route_to_approval()`, approval polling to orchestrator |
| 10 | Set up cron jobs | 15 min | `crontab -e` — add daily dashboard refresh + weekly briefing |

---

## 9. Resource Requirements

### External Services / Accounts

| Service | Required? | Cost | Setup Time | Link |
|---------|-----------|------|------------|------|
| Google Cloud (Gmail API) | Yes | Free | 1 hour | https://console.cloud.google.com |
| LinkedIn Developer App | Yes | Free | 10 min + approval wait | https://www.linkedin.com/developers/apps |
| Twilio (WhatsApp) | Optional | Free trial ($15 credit) | 30 min | https://www.twilio.com |
| ngrok | If using Twilio | Free tier sufficient | 10 min | https://ngrok.com |

### Python Dependencies (Added)

```toml
# Production
"google-api-python-client>=2.100.0"   # Gmail API client
"google-auth-oauthlib>=1.2.0"         # OAuth2 flow
"google-auth-httplib2>=0.2.0"         # HTTP transport
"mcp>=1.0.0"                          # MCP server SDK
"flask>=3.0.0"                        # WhatsApp webhook server
"twilio>=9.0.0"                       # Twilio WhatsApp SDK

# Dev (already have pytest)
# No new dev dependencies needed
```

Install all at once:
```bash
uv add google-api-python-client google-auth-oauthlib google-auth-httplib2 mcp flask twilio
```

### Documentation Links

| Resource | URL |
|----------|-----|
| Gmail API Quickstart | https://developers.google.com/gmail/api/quickstart/python |
| Gmail API Reference | https://developers.google.com/gmail/api/reference/rest |
| MCP Python SDK | https://github.com/modelcontextprotocol/python-sdk |
| MCP Specification | https://spec.modelcontextprotocol.io/ |
| Claude Code MCP Config | https://docs.anthropic.com/en/docs/agents-and-tools/mcp |
| Agent Skills Docs | https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills |
| Twilio WhatsApp Sandbox | https://www.twilio.com/docs/whatsapp/sandbox |
| LinkedIn Share API | https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares |
| Flask Quickstart | https://flask.palletsprojects.com/en/stable/quickstart/ |

---

## 10. Success Metrics

### Requirement Verification Matrix

| Req | Description | How to Verify | Pass Criteria |
|-----|-------------|---------------|---------------|
| S1 | Bronze requirements | `uv run pytest tests/test_config.py tests/test_utils.py tests/test_watcher.py tests/test_orchestrator.py -v` | All 69 original tests pass |
| S2 | Two+ Watchers | `ls src/gmail_watcher.py src/whatsapp_watcher.py` + run both | Both start without errors, create files in `/Inbox/` |
| S3 | LinkedIn posting | `uv run python -m src.linkedin_poster` | Approval file created in `/Pending_Approval/` with post content |
| S4 | Plan.md reasoning | Drop invoice.pdf in `/Inbox/`, wait for processing | `ls AI_Employee_Vault/Plans/PLAN_*.md` shows plan file with steps |
| S5 | MCP server | `claude mcp list` | "email" server listed; `send_email` tool creates approval file |
| S6 | HITL workflow | Process a high-priority invoice | File appears in `/Pending_Approval/`; moving to `/Approved/` completes it |
| S7 | Scheduling | `crontab -l` | At least one cron entry exists; `--once` flag works |
| S8 | All AI as Skills | `ls .claude/skills/` | 9 skill directories, each with SKILL.md |

### Quantitative Targets

| Metric | Bronze (Current) | Silver (Target) |
|--------|-----------------|-----------------|
| Tests passing | 69 | 116+ |
| Agent Skills | 3 | 9 |
| Watchers | 1 (file system) | 3 (file + Gmail + WhatsApp) |
| MCP servers | 0 | 1 (email) |
| Vault folders | 6 | 11 |
| Cron jobs | 0 | 2-3 |
| Source files | 4 | 10 |

### Demo Checklist (5-10 minute video)

1. Show all processes starting (`scripts/start_silver.sh`)
2. Drop a file in `/Inbox/` — show it processed to `/Done/` (existing Bronze flow)
3. Send yourself an email — show Gmail watcher picking it up
4. Show Plan.md created for an invoice document
5. Show a high-priority item routed to `/Pending_Approval/`
6. Approve it in Obsidian — show it complete in `/Done/`
7. Run LinkedIn poster — show approval file with generated content
8. Show cron jobs (`crontab -l`)
9. Show MCP server listed (`claude mcp list`)
10. Show all 9 Agent Skills (`ls .claude/skills/`)
