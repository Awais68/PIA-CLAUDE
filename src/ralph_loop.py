"""Ralph Wiggum Loop — Zoya's self-monitoring system. Gold Tier G2.

Named after Ralph Wiggum ("I'm in danger!"), this module detects when
the system is stuck, confused, or failing repeatedly.

It creates RALPH_*.md alert files in Pending_Approval/ for human review.

Checks performed:
1. Files stuck in In_Progress too long (default: 15 minutes)
2. High quarantine count (items repeatedly failing)
3. Large pending approval backlog (items waiting human review)
4. Stale pending queue (items waiting too long to be processed)
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import (
    IN_PROGRESS,
    NEEDS_ACTION,
    PENDING_APPROVAL,
    QUARANTINE,
)
from src.utils import log_action, setup_logger

logger = setup_logger("ralph_loop")

# Thresholds
STUCK_IN_PROGRESS_MINUTES = 15
HIGH_QUARANTINE_COUNT = 3
HIGH_APPROVAL_BACKLOG = 5
STALE_PENDING_HOURS = 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_frontmatter(path: Path) -> dict[str, str]:
    """Parse YAML-ish frontmatter from a .md file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def _parse_timestamp(ts_str: str) -> datetime | None:
    """Parse an ISO timestamp string, returning None on failure."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _mtime_as_utc(path: Path) -> datetime:
    """Get file modification time as UTC datetime."""
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _count_files(folder: Path) -> int:
    """Count non-gitkeep files in a folder."""
    if not folder.exists():
        return 0
    return len([f for f in folder.iterdir() if f.is_file() and f.name != ".gitkeep"])


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_stuck_in_progress(timeout_minutes: int = STUCK_IN_PROGRESS_MINUTES) -> list[dict]:
    """Find files that have been in In_Progress too long.

    Returns list of dicts describing stuck items.
    """
    if not IN_PROGRESS.exists():
        return []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=timeout_minutes)
    stuck = []

    for f in IN_PROGRESS.glob("FILE_*.md"):
        mtime = _mtime_as_utc(f)
        if mtime < cutoff:
            fm = _read_frontmatter(f)
            age_minutes = int((now - mtime).total_seconds() / 60)
            stuck.append({
                "file": f.name,
                "original_name": fm.get("original_name", f.name),
                "source": fm.get("source", "file_drop"),
                "age_minutes": age_minutes,
                "mtime": mtime.isoformat(),
            })

    return stuck


def check_quarantine_count(threshold: int = HIGH_QUARANTINE_COUNT) -> dict:
    """Check if quarantine count exceeds threshold.

    Returns dict with count and whether alert should fire.
    """
    count = _count_files(QUARANTINE)
    # Count only .md files that aren't reason files
    md_count = 0
    if QUARANTINE.exists():
        md_count = len([
            f for f in QUARANTINE.glob("*.md")
            if not f.name.endswith(".reason.md")
        ])
    return {
        "count": md_count,
        "threshold": threshold,
        "alert": md_count >= threshold,
    }


def check_approval_backlog(threshold: int = HIGH_APPROVAL_BACKLOG) -> dict:
    """Check if pending approval queue is too large.

    Returns dict with count and whether alert should fire.
    """
    count = _count_files(PENDING_APPROVAL)
    return {
        "count": count,
        "threshold": threshold,
        "alert": count >= threshold,
    }


def check_stale_pending(max_age_hours: int = STALE_PENDING_HOURS) -> list[dict]:
    """Find files that have been in Needs_Action too long without processing.

    Returns list of stale items.
    """
    if not NEEDS_ACTION.exists():
        return []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max_age_hours)
    stale = []

    for f in NEEDS_ACTION.glob("FILE_*.md"):
        fm = _read_frontmatter(f)
        if fm.get("status") != "pending":
            continue
        # Use queued_at from frontmatter if available
        queued_at = _parse_timestamp(fm.get("queued_at", ""))
        if queued_at is None:
            queued_at = _mtime_as_utc(f)
        if queued_at < cutoff:
            age_hours = int((now - queued_at).total_seconds() / 3600)
            stale.append({
                "file": f.name,
                "original_name": fm.get("original_name", f.name),
                "source": fm.get("source", "file_drop"),
                "age_hours": age_hours,
                "queued_at": queued_at.isoformat(),
            })

    return stale


# ---------------------------------------------------------------------------
# Alert creator
# ---------------------------------------------------------------------------

def create_ralph_alert(alert_type: str, details: str, severity: str = "warning") -> Path:
    """Create a RALPH_*.md alert file in Pending_Approval/ for human review.

    Args:
        alert_type: Short identifier (e.g. "stuck_in_progress")
        details: Human-readable description of the problem.
        severity: "warning" or "critical"

    Returns:
        Path to the created alert file.
    """
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    filename = f"RALPH_{now.strftime('%Y%m%d_%H%M%S')}_{alert_type}.md"
    alert_path = PENDING_APPROVAL / filename

    content = (
        f"---\n"
        f"type: ralph_alert\n"
        f"alert_type: {alert_type}\n"
        f"severity: {severity}\n"
        f"created_at: {now.isoformat()}\n"
        f"status: pending_review\n"
        f"---\n\n"
        f"# Ralph Alert: {alert_type.replace('_', ' ').title()}\n\n"
        f"**Severity:** {severity.upper()}  \n"
        f"**Detected at:** {now.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"## What Happened\n\n"
        f"{details}\n\n"
        f"## Recommended Action\n\n"
        + _get_recommendation(alert_type)
        + "\n\n"
        f"---\n"
        f"*This alert was generated by Zoya's Ralph Wiggum self-monitoring system.*\n"
        f"*Move this file to Approved/ to acknowledge, or Rejected/ to dismiss.*\n"
    )

    alert_path.write_text(content, encoding="utf-8")
    log_action("ralph_alert_created", str(alert_path), {
        "alert_type": alert_type,
        "severity": severity,
    })
    logger.warning("Ralph alert: %s (%s)", alert_type, severity)
    return alert_path


def _get_recommendation(alert_type: str) -> str:
    """Return actionable recommendations for each alert type."""
    recommendations = {
        "stuck_in_progress": (
            "1. Check if the orchestrator process is running.\n"
            "2. Inspect files in `AI_Employee_Vault/In_Progress/`.\n"
            "3. If stuck, manually move the file back to `Needs_Action/` "
            "and reset its frontmatter `status` to `pending`.\n"
            "4. Check logs in `AI_Employee_Vault/Logs/` for errors."
        ),
        "high_quarantine": (
            "1. Review files in `AI_Employee_Vault/Quarantine/`.\n"
            "2. Check the `.reason.md` files to understand failures.\n"
            "3. Fix the underlying issue (bad file format, API error, etc.).\n"
            "4. Re-drop corrected files in `Inbox/` if needed."
        ),
        "approval_backlog": (
            "1. Open `AI_Employee_Vault/Pending_Approval/` in Obsidian.\n"
            "2. Review each item and move to `Approved/` or `Rejected/`.\n"
            "3. The orchestrator will complete approved items on its next cycle."
        ),
        "stale_pending": (
            "1. Check if the orchestrator is running: `uv run zoya-orchestrator`.\n"
            "2. Check if the AI provider is accessible (Claude/Qwen/Ollama).\n"
            "3. Run a single cycle manually: `uv run zoya-orchestrator --once`."
        ),
    }
    return recommendations.get(
        alert_type,
        "1. Review the issue described above.\n2. Take appropriate corrective action.",
    )


# ---------------------------------------------------------------------------
# Main check runner
# ---------------------------------------------------------------------------

def run_ralph_checks(
    stuck_timeout_minutes: int = STUCK_IN_PROGRESS_MINUTES,
    quarantine_threshold: int = HIGH_QUARANTINE_COUNT,
    approval_threshold: int = HIGH_APPROVAL_BACKLOG,
    stale_hours: int = STALE_PENDING_HOURS,
) -> list[Path]:
    """Run all Ralph checks and create alerts for any issues found.

    Returns list of alert files created (empty = all clear).
    """
    alerts_created = []

    # Check 1: Files stuck in In_Progress
    stuck = check_stuck_in_progress(stuck_timeout_minutes)
    if stuck:
        names = ", ".join(i["original_name"] for i in stuck[:3])
        extra = f" (and {len(stuck) - 3} more)" if len(stuck) > 3 else ""
        details = (
            f"The following file(s) have been stuck in `In_Progress/` for more than "
            f"{stuck_timeout_minutes} minutes:\n\n"
            + "\n".join(
                f"- **{i['original_name']}** — {i['age_minutes']} minutes "
                f"(source: {i['source']})"
                for i in stuck
            )
        )
        severity = "critical" if any(i["age_minutes"] > 60 for i in stuck) else "warning"
        alert_path = create_ralph_alert("stuck_in_progress", details, severity)
        alerts_created.append(alert_path)

    # Check 2: High quarantine count
    q_check = check_quarantine_count(quarantine_threshold)
    if q_check["alert"]:
        details = (
            f"**{q_check['count']} item(s)** are in `Quarantine/`, which exceeds the "
            f"threshold of {q_check['threshold']}. These items have failed processing "
            f"multiple times and need manual review."
        )
        alert_path = create_ralph_alert("high_quarantine", details, "warning")
        alerts_created.append(alert_path)

    # Check 3: Approval backlog
    a_check = check_approval_backlog(approval_threshold)
    if a_check["alert"]:
        details = (
            f"**{a_check['count']} item(s)** are waiting in `Pending_Approval/`, "
            f"which exceeds the threshold of {a_check['threshold']}. "
            f"These items need human review before they can be completed."
        )
        alert_path = create_ralph_alert("approval_backlog", details, "warning")
        alerts_created.append(alert_path)

    # Check 4: Stale pending items
    stale = check_stale_pending(stale_hours)
    if stale:
        details = (
            f"The following file(s) have been waiting in `Needs_Action/` for more than "
            f"{stale_hours} hour(s) without being processed:\n\n"
            + "\n".join(
                f"- **{i['original_name']}** — {i['age_hours']}h "
                f"(source: {i['source']})"
                for i in stale
            )
        )
        alert_path = create_ralph_alert("stale_pending", details, "warning")
        alerts_created.append(alert_path)

    if alerts_created:
        logger.warning("Ralph found %d issue(s) — alerts created", len(alerts_created))
    else:
        logger.info("Ralph checks passed — all systems nominal")

    return alerts_created


def get_system_status() -> dict:
    """Return a summary of the current system health status."""
    stuck = check_stuck_in_progress()
    q_check = check_quarantine_count()
    a_check = check_approval_backlog()
    stale = check_stale_pending()

    issues = (
        len(stuck)
        + (1 if q_check["alert"] else 0)
        + (1 if a_check["alert"] else 0)
        + len(stale)
    )

    return {
        "status": "ok" if issues == 0 else "warning",
        "issues": issues,
        "stuck_in_progress": len(stuck),
        "quarantine_count": q_check["count"],
        "approval_backlog": a_check["count"],
        "stale_pending": len(stale),
    }
