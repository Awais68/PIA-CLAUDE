# Quick Start Guide — Silver Tier

**Date:** 2026-02-15
**Prerequisite:** Bronze Tier COMPLETE (69 tests passing)
**Time to first working feature:** ~3 hours

---

## Prerequisites Checklist

Before writing any code, verify these are in place:

- [x] **Python 3.13+** installed
  ```bash
  python3 --version  # Should be 3.13+
  ```
- [x] **uv** package manager installed
  ```bash
  uv --version
  ```
- [x] **Claude Code** active subscription
  ```bash
  claude --version
  ```
- [x] **Bronze Tier passing** — all 69 tests green
  ```bash
  uv run pytest tests/ -v  # All 69 should pass
  ```
- [x] **Obsidian** installed with vault at `AI_Employee_Vault/`
- [x] **Git** repo initialized and clean
  ```bash
  git status  # Should be on main branch
  ```
- [ ] **Google account** for Gmail API (any Gmail account works)
- [ ] **LinkedIn account** for Developer API access

---

## First 3 Tasks to Do TODAY

### Task 1: Create Silver Vault Folders + Update Config (30 min)

This unblocks everything else. Zero external dependencies.

**Step 1:** Create the 5 new vault folders:
```bash
cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"

mkdir -p AI_Employee_Vault/{Plans,Pending_Approval,Approved,Rejected,Briefings}
touch AI_Employee_Vault/{Plans,Pending_Approval,Approved,Rejected,Briefings}/.gitkeep
```

**Step 2:** Add Silver paths to `src/config.py`. Open the file and add after the existing path definitions:

```python
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
LINKEDIN_DRY_RUN = True  # safety default — set to False when API access is ready
```

**Step 3:** Update `.gitignore` — add these lines:
```
# Silver tier vault folders
AI_Employee_Vault/Plans/*
AI_Employee_Vault/Pending_Approval/*
AI_Employee_Vault/Approved/*
AI_Employee_Vault/Rejected/*
AI_Employee_Vault/Briefings/*
!AI_Employee_Vault/*/.gitkeep
```

**Verify it worked:**
```bash
# Should show 11 folders (6 Bronze + 5 Silver)
ls AI_Employee_Vault/

# Should still pass all 69 tests
uv run pytest tests/ -v
```

---

### Task 2: Implement Plan.md Reasoning Loop — S4 (2 hours)

This is the highest-value quick win. No external APIs needed.

**Step 1:** Create the plan-creator skill:
```bash
mkdir -p .claude/skills/plan-creator
```

Then create `.claude/skills/plan-creator/SKILL.md` with the full skill spec (see `Silver_Tier_Blueprint.md` section 3, Task 1.2 for the complete content).

**Step 2:** Add these functions to `src/orchestrator.py`:

```python
def should_create_plan(meta_path: Path) -> bool:
    """Determine if this task warrants a Plan.md."""
    fm = _read_frontmatter(meta_path)
    doc_type = fm.get("type", "other")
    priority = fm.get("priority", "low")
    return doc_type in ("invoice", "contract", "proposal") or priority == "high"


def create_plan(meta_path: Path, companion: Path | None) -> Path | None:
    """Invoke Claude to create a Plan.md for this task."""
    from src.config import PLANS
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
        return plan_path
    logger.warning("Plan creation failed (non-critical), proceeding without plan")
    return None
```

**Step 3:** In `run_cycle()`, add before the `process_with_claude()` call:
```python
if should_create_plan(claimed_meta):
    create_plan(claimed_meta, claimed_companion)
```

**Step 4:** Write tests in `tests/test_plan_creator.py`.

**Verify it worked:**
```bash
# Run the new tests
uv run pytest tests/test_plan_creator.py -v

# Manual test: drop an invoice PDF in Inbox
cp ~/some-invoice.pdf AI_Employee_Vault/Inbox/

# Start watcher + orchestrator, then check:
ls AI_Employee_Vault/Plans/  # Should have a PLAN_*.md file
```

---

### Task 3: Apply for LinkedIn API Access (10 min)

Do this NOW because approval takes days. You can build everything else while waiting.

**Step 1:** Go to https://www.linkedin.com/developers/apps

**Step 2:** Click "Create App"
- App name: "Zoya AI Employee"
- LinkedIn Page: your company/personal page
- App logo: any image
- Legal agreement: accept

**Step 3:** Go to the "Auth" tab
- Note your Client ID and Client Secret
- Add redirect URL: `http://localhost:8080/callback`

**Step 4:** Go to "Products" tab
- Request access to "Share on LinkedIn" (provides `w_member_social` scope)
- This may require review — submit and wait

**Step 5:** Save credentials to `.env`:
```bash
echo "LINKEDIN_CLIENT_ID=your_client_id_here" >> .env
echo "LINKEDIN_CLIENT_SECRET=your_client_secret_here" >> .env
echo "LINKEDIN_DRY_RUN=true" >> .env
```

**Verify:** Check your email for LinkedIn Developer approval (may take 1-7 days). In the meantime, LinkedIn features will work in dry-run mode.

---

## What to Do Next (After Today)

After completing the 3 tasks above, follow the `Silver_Execution_Plan.md` for the detailed week-by-week plan:

| Next Priority | What | Est. Time |
|---------------|------|-----------|
| **Tomorrow** | HITL Approval Workflow (S6) | 4h |
| **Day 3** | Google Cloud setup + Gmail deps | 3h |
| **Day 4** | Gmail Watcher implementation | 4h |
| **Day 5** | Email MCP Server | 4h |
| **Day 6** | LinkedIn poster + cron | 4h |

---

## How to Verify Each Silver Requirement

Quick commands to check your progress at any time:

```bash
# S1: Bronze still works
uv run pytest tests/test_config.py tests/test_utils.py tests/test_watcher.py tests/test_orchestrator.py -v

# S2: Two+ watchers exist
ls src/gmail_watcher.py src/watchers/whatsapp_watcher.py 2>/dev/null || ls src/watchers/gmail_watcher.py src/watchers/whatsapp_watcher.py

# S3: LinkedIn poster
uv run python -m src.linkedin_poster 2>/dev/null && echo "OK" || echo "Not implemented yet"

# S4: Plan.md
ls AI_Employee_Vault/Plans/PLAN_*.md 2>/dev/null && echo "Plans exist" || echo "No plans yet"

# S5: MCP server
claude mcp list 2>/dev/null | grep -q email && echo "MCP OK" || echo "MCP not configured"

# S6: HITL workflow
ls AI_Employee_Vault/Pending_Approval/ AI_Employee_Vault/Approved/ AI_Employee_Vault/Rejected/ 2>/dev/null && echo "HITL folders exist" || echo "Missing HITL folders"

# S7: Scheduling
crontab -l 2>/dev/null | grep -q "orchestrator" && echo "Cron OK" || echo "No cron jobs"

# S8: All skills
echo "Skills: $(ls .claude/skills/ | wc -l) (need 9)"
```

---

## Where to Get Help If Stuck

| Problem | Solution |
|---------|----------|
| Gmail OAuth consent screen issues | Use "Desktop app" credential type + add yourself as test user |
| `credentials.json` not found | Download from Google Cloud Console > APIs & Services > Credentials |
| Token expired during testing | Delete `token.json` and re-run — will trigger new browser auth |
| MCP server not showing in Claude | Check `.claude/mcp.json` exists and path is correct |
| Tests failing after changes | Run `uv run pytest tests/ -v --tb=long` for detailed error output |
| LinkedIn API access pending | Use `LINKEDIN_DRY_RUN=true` in the meantime — still demonstrates flow |
| WhatsApp webhook unreachable | Make sure ngrok is running: `ngrok http 5001` |
| Orchestrator won't start | Check for PID lock file: `ls *.lock.pid` and delete if stale |
| Import errors | Run `uv sync` to install all dependencies |

### Reference Documents
- `Silver_Tier_Blueprint.md` — complete technical spec with code samples
- `SilverRoadmap.md` — gap analysis and priority order
- `silverRequirements.md` — official requirements from hackathon spec
- `Implementation_Priority.md` — what to build in what order
- `Silver_Execution_Plan.md` — week-by-week breakdown
- `AGENTS.md` — architecture reference
- `config/credentials.example.json` — what secrets you need
