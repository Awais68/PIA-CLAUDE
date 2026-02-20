---
skill_name: LogJanitor
version: 1.0
trigger: "Every Sunday 11:30 PM via cron — always runs 30 minutes AFTER CEOBriefing completes"
inputs:
  - AI_Employee_Vault/Logs/YYYY-MM-DD.json    # structured audit logs
  - AI_Employee_Vault/Logs/YYYY-MM-DD.log     # human-readable text logs
outputs:
  - Deletes log files older than LOG_RETENTION_DAYS (default 90)
  - Appends deletion summary to AI_Employee_Vault/Logs/gold_tier_progress.md
approval_required: "no — fully automated; dry-run available"
max_runtime: 2
---

## Objective

Delete audit log files older than the retention window so disk usage stays bounded.
This skill is the ONLY place log deletion happens — no other skill or module should
call `purge_old_logs()` or delete files from `Logs/`.

> Separation of concerns: CEOBriefing **reads** logs. LogJanitor **cleans** logs.

---

## Step-by-Step Process

1. **List** all `*.json` and `*.log` files in `AI_Employee_Vault/Logs/`

2. **Parse date** from each filename (`YYYY-MM-DD.json` or `YYYY-MM-DD.log`)
   - Skip files that don't match the date pattern (e.g. `gold_tier_progress.md`, `.cross_domain_processed.json`)
   - Skip the current day's log (never delete today's active log)

3. **Check age** — if file date < today - `LOG_RETENTION_DAYS`:
   - In `--dry-run` mode: print `[DRY RUN] Would delete: YYYY-MM-DD.json (N days old)`
   - In live mode: delete the file, record filename + size in deletion list

4. **If a file is locked / in use** (OS error on delete):
   - Skip the file
   - Log warning: `[WARN] Could not delete YYYY-MM-DD.json — skipped (file in use)`
   - Continue with remaining files

5. **Append summary** to `AI_Employee_Vault/Logs/gold_tier_progress.md`:
   ```markdown
   | YYYY-MM-DD HH:MM | log_janitor | Ns | deleted=N files (X MB freed) |
   ```

6. **Print summary** to stdout:
   ```
   LogJanitor: deleted 3 files (2.1 MB freed). Oldest retained: 2025-11-22.
   ```

---

## What LogJanitor Does NOT Touch

- `gold_tier_progress.md` — permanent record, never deleted
- `.cross_domain_processed.json` — state file, never deleted
- `.seen_hashes.json` — bank dedup state, never deleted
- `Archive/Bank/` — bank statement archive, never deleted
- Any file that does not match `YYYY-MM-DD.json` or `YYYY-MM-DD.log` pattern

---

## .env Variables

```bash
LOG_RETENTION_DAYS=90    # delete logs older than this many days (default: 90)
LOG_DRY_RUN=false        # true = show what would be deleted without deleting
```

---

## Success Criteria

- No log files older than `LOG_RETENTION_DAYS` remain after run
- `gold_tier_progress.md` updated with `log_janitor` entry
- Locked/in-use files are skipped with a warning (not a failure)
- `--dry-run` produces output without deleting anything
- Run completes within `max_runtime` (2 minutes)

---

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Filename doesn't match date pattern | Skip file, continue |
| File locked or in use | Skip file, log warning, continue |
| `Logs/` directory missing | Log warning and exit cleanly (nothing to do) |
| `gold_tier_progress.md` not writable | Log to stderr, continue (non-fatal) |
| All logs within retention window | Print "Nothing to delete" and exit |

---

## Cron Setup

```bash
# Sunday 11:30 PM — AFTER CEOBriefing (0 23 * * 0)
30 23 * * 0 cd /path/to/project && uv run python -m src.log_janitor
```

---

## CLI

```bash
# Normal run (delete logs older than 90 days)
uv run python -m src.log_janitor

# Dry run — show what would be deleted, delete nothing
uv run python -m src.log_janitor --dry-run

# Use a custom retention window
uv run python -m src.log_janitor --retention-days 30

# Dry run with custom retention
uv run python -m src.log_janitor --dry-run --retention-days 30
```
