# Ralph Wiggum Monitor Skill

## Purpose
Self-monitoring system that detects when Zoya is stuck, confused, or failing
repeatedly. Creates RALPH_*.md alert files in Pending_Approval/ for human review.

Named after Ralph Wiggum ("I'm in danger!") — this skill makes Zoya aware of her
own operational health and proactively signals when human intervention is needed.

## When This Skill Is Used
- Integrated into orchestrator's `run_cycle()` (runs every cycle)
- Can be invoked manually: `uv run python -c "from src.ralph_loop import run_ralph_checks; run_ralph_checks()"`
- Scheduled via JobScheduler for periodic checks

## Checks Performed

### 1. Stuck In Progress (Critical)
Detects files that have been in `In_Progress/` for more than 15 minutes.
This usually means the AI provider crashed or the orchestrator is frozen.

**Alert created:** `RALPH_<timestamp>_stuck_in_progress.md`

### 2. High Quarantine Count (Warning)
Detects when 3 or more items are in `Quarantine/`, indicating systemic
processing failures (bad files, API errors, etc.).

**Alert created:** `RALPH_<timestamp>_high_quarantine.md`

### 3. Approval Backlog (Warning)
Detects when 5 or more items are waiting in `Pending_Approval/` without
human review. The system is blocked on human action.

**Alert created:** `RALPH_<timestamp>_approval_backlog.md`

### 4. Stale Pending Queue (Warning)
Detects when files have been waiting in `Needs_Action/` for more than 2 hours
without being processed, indicating the orchestrator may be down.

**Alert created:** `RALPH_<timestamp>_stale_pending.md`

## Alert Format
All alerts are created in `Pending_Approval/` with:
- YAML frontmatter: type, severity, alert_type, created_at
- Clear description of what went wrong
- Actionable recommendations with specific steps
- Instruction to move to Approved/ (acknowledge) or Rejected/ (dismiss)

## Severity Levels
- `warning` — action recommended but system still operational
- `critical` — system is likely stuck and requires immediate attention

## Human Response
1. Open the RALPH_*.md file in Obsidian
2. Read the "What Happened" and "Recommended Action" sections
3. Take corrective action (restart orchestrator, fix files, etc.)
4. Move the alert file to `Approved/` (acknowledged) or `Rejected/` (dismissed)
5. The orchestrator will clean up on its next cycle

## Thresholds (configurable in src/ralph_loop.py)
| Check | Default |
|-------|---------|
| Stuck in progress | > 15 minutes |
| High quarantine | >= 3 items |
| Approval backlog | >= 5 items |
| Stale pending | > 2 hours |
