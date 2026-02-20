"""Comprehensive Audit Logger for Zoya — Gold Tier Task 8.

Log format (JSON-lines, one entry per line):
{
  "timestamp":       "ISO8601",
  "action_type":     "email_send|payment|social_post|invoice_create|...",
  "actor":           "claude_code|human|watcher",
  "target":          "recipient/system",
  "parameters":      {},
  "approval_status": "auto|human_approved|human_rejected",
  "approved_by":     "human|auto_rule",
  "result":          "success|failure|pending",
  "error":           null
}

Storage:
  - Logs saved to AI_Employee_Vault/Logs/YYYY-MM-DD.json
  - Retention: 90 days minimum (old logs auto-purged)
  - Weekly summary appended to Dashboard.md every Sunday

Usage:
    from src.audit_logger import audit_log, weekly_audit_summary, purge_old_logs
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.config import DASHBOARD, LOGS, VAULT_PATH
from src.utils import setup_logger

logger = setup_logger("audit_logger")

LOG_RETENTION_DAYS = 90

# All recognised action types — for documentation / validation
ACTION_TYPES = frozenset({
    # Document processing
    "file_queued", "file_claimed", "file_done", "file_retry", "file_quarantined",
    "file_routed_to_approval", "file_approved", "file_rejected",
    # Email
    "email_send", "email_send_approved", "email_send_rejected",
    "email_received", "email_processed",
    # Payments
    "payment_initiated", "payment_approved", "payment_rejected",
    "payment_error", "invoice_create", "invoice_sent",
    # Social
    "social_post", "social_post_approved", "social_post_rejected",
    "twitter_post", "linkedin_post", "facebook_post", "instagram_post",
    "social_metrics_fetched",
    # WhatsApp
    "whatsapp_received", "whatsapp_sent",
    # Contacts
    "contact_created", "contact_updated",
    # System
    "orchestrator_started", "orchestrator_stopped",
    "briefing_generated", "audit_generated",
    "auth_error_alert_created", "payment_error_alert_created",
    "component_failure", "component_recovered",
    "error_recovery_attempt", "offline_queued", "offline_flushed",
    "ralph_alert_created", "ralph_wiggum_started", "ralph_wiggum_completed",
    "plan_created", "hitl_evaluated",
})


# ---------------------------------------------------------------------------
# Core log writer
# ---------------------------------------------------------------------------

def audit_log(
    action_type: str,
    target: str,
    *,
    actor: str = "claude_code",
    parameters: dict[str, Any] | None = None,
    approval_status: str = "auto",
    approved_by: str = "auto_rule",
    result: str = "success",
    error: str | None = None,
) -> None:
    """Append a structured audit entry to today's JSON-lines log.

    Args:
        action_type:     What happened (see ACTION_TYPES for valid values).
        target:          The recipient, file path, or system affected.
        actor:           Who triggered the action ("claude_code" | "human" | "watcher").
        parameters:      Arbitrary context dict (amounts, IDs, etc.).
        approval_status: "auto" | "human_approved" | "human_rejected".
        approved_by:     "human" | "auto_rule" | name of approver.
        result:          "success" | "failure" | "pending".
        error:           Error message string, or None on success.
    """
    LOGS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    log_file = LOGS / f"{today}.json"

    entry: dict[str, Any] = {
        "timestamp": now.isoformat(),
        "action_type": action_type,
        "actor": actor,
        "target": target,
        "parameters": parameters or {},
        "approval_status": approval_status,
        "approved_by": approved_by,
        "result": result,
        "error": error,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Log reader
# ---------------------------------------------------------------------------

def read_logs(
    date: datetime | None = None,
    days: int = 1,
    action_type_filter: str | None = None,
    result_filter: str | None = None,
    actor_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Read and optionally filter audit log entries.

    Args:
        date:                End date for the range (defaults to today UTC).
        days:                How many days back to read (default 1 = today only).
        action_type_filter:  Only return entries with this action_type.
        result_filter:       Only return entries with this result.
        actor_filter:        Only return entries with this actor.

    Returns:
        List of log entry dicts, chronologically ordered.
    """
    end = (date or datetime.now(timezone.utc)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    entries: list[dict] = []

    for i in range(days):
        day = end - timedelta(days=i)
        log_file = LOGS / f"{day.strftime('%Y-%m-%d')}.json"
        if not log_file.exists():
            continue
        for line in log_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if action_type_filter and entry.get("action_type") != action_type_filter:
                continue
            if result_filter and entry.get("result") != result_filter:
                continue
            if actor_filter and entry.get("actor") != actor_filter:
                continue
            entries.append(entry)

    return sorted(entries, key=lambda e: e.get("timestamp", ""))


# ---------------------------------------------------------------------------
# Retention: purge logs older than 90 days
# ---------------------------------------------------------------------------

def purge_old_logs(retention_days: int = LOG_RETENTION_DAYS) -> int:
    """Delete log files older than retention_days.

    Args:
        retention_days: Minimum age in days before a log file is deleted.

    Returns:
        Number of files deleted.
    """
    if not LOGS.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = 0

    for log_file in LOGS.glob("*.json"):
        # Parse the date from the filename (YYYY-MM-DD.json)
        try:
            file_date = datetime.strptime(log_file.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if file_date < cutoff:
            log_file.unlink()
            deleted += 1
            logger.info("Purged old log: %s", log_file.name)

    if deleted:
        audit_log("log_purge", "LOGS/", parameters={"files_deleted": deleted, "retention_days": retention_days})
    return deleted


# ---------------------------------------------------------------------------
# Weekly summary builder
# ---------------------------------------------------------------------------

def weekly_audit_summary(
    append_to_dashboard: bool = True,
) -> str:
    """Generate a markdown weekly summary from the last 7 days of audit logs.

    Args:
        append_to_dashboard: If True, appends the summary block to Dashboard.md.

    Returns:
        The generated markdown summary string.
    """
    entries = read_logs(days=7)

    # Tally by action_type
    action_counts: dict[str, int] = {}
    result_counts: dict[str, int] = {"success": 0, "failure": 0, "pending": 0}
    actor_counts: dict[str, int] = {"claude_code": 0, "human": 0, "watcher": 0}
    approval_counts: dict[str, int] = {"auto": 0, "human_approved": 0, "human_rejected": 0}
    failures: list[dict] = []

    for e in entries:
        at = e.get("action_type", "unknown")
        action_counts[at] = action_counts.get(at, 0) + 1

        r = e.get("result", "success")
        result_counts[r] = result_counts.get(r, 0) + 1

        ac = e.get("actor", "claude_code")
        actor_counts[ac] = actor_counts.get(ac, 0) + 1

        ap = e.get("approval_status", "auto")
        approval_counts[ap] = approval_counts.get(ap, 0) + 1

        if r == "failure":
            failures.append(e)

    # Top 10 action types
    top_actions = sorted(action_counts.items(), key=lambda x: -x[1])[:10]
    action_table = "\n".join(
        f"| {at} | {cnt} |" for at, cnt in top_actions
    ) or "| (none) | 0 |"

    # Recent failures (last 5)
    recent_failures = failures[-5:]
    failure_lines = "\n".join(
        f"- `{e.get('timestamp','')[:19]}` [{e.get('action_type')}] "
        f"→ {e.get('target','')[:50]} — {e.get('error','')[:80]}"
        for e in recent_failures
    ) or "_No failures this week_ ✅"

    now = datetime.now(timezone.utc)
    summary = (
        f"\n---\n\n"
        f"## 📊 Weekly Audit Summary — {now.strftime('%Y-%m-%d')}\n\n"
        f"**Period:** Last 7 days ({len(entries)} total log entries)\n\n"
        f"### Results\n\n"
        f"| Result | Count |\n|--------|-------|\n"
        f"| Success | {result_counts['success']} |\n"
        f"| Failure | {result_counts['failure']} |\n"
        f"| Pending | {result_counts['pending']} |\n\n"
        f"### Actor Breakdown\n\n"
        f"| Actor | Actions |\n|-------|--------|\n"
        f"| Claude Code (AI) | {actor_counts['claude_code']} |\n"
        f"| Human | {actor_counts['human']} |\n"
        f"| Watcher | {actor_counts['watcher']} |\n\n"
        f"### Approval Breakdown\n\n"
        f"| Mode | Count |\n|------|-------|\n"
        f"| Auto | {approval_counts['auto']} |\n"
        f"| Human Approved | {approval_counts['human_approved']} |\n"
        f"| Human Rejected | {approval_counts['human_rejected']} |\n\n"
        f"### Top 10 Action Types\n\n"
        f"| Action | Count |\n|--------|-------|\n"
        f"{action_table}\n\n"
        f"### Recent Failures\n\n"
        f"{failure_lines}\n\n"
        f"_Generated by Zoya Audit Logger at {now.isoformat()}_\n"
    )

    if append_to_dashboard and DASHBOARD.exists():
        existing = DASHBOARD.read_text(encoding="utf-8")
        # Remove any previous weekly summary block
        existing = re.sub(
            r"\n---\n\n## 📊 Weekly Audit Summary.*",
            "",
            existing,
            flags=re.DOTALL,
        )
        DASHBOARD.write_text(existing + summary, encoding="utf-8")
        logger.info("Weekly audit summary appended to Dashboard.md")
        audit_log("audit_summary_generated", "Dashboard.md", parameters={"entries": len(entries)})

    return summary


# ---------------------------------------------------------------------------
# Summary stats (used by CEO briefing)
# ---------------------------------------------------------------------------

def get_period_stats(days: int = 7) -> dict[str, Any]:
    """Return aggregated stats for the last N days for the CEO briefing.

    Args:
        days: Number of days to look back.

    Returns:
        Dict with counts and failure details.
    """
    entries = read_logs(days=days)

    social_posts = [e for e in entries if "social_post" in e.get("action_type", "")
                    or e.get("action_type", "").startswith(("twitter_", "linkedin_",
                                                              "facebook_", "instagram_"))]
    emails_sent = [e for e in entries if e.get("action_type") == "email_send"
                   and e.get("result") == "success"]
    payments = [e for e in entries if "payment" in e.get("action_type", "")]
    failures = [e for e in entries if e.get("result") == "failure"]

    return {
        "total_entries": len(entries),
        "social_posts": len(social_posts),
        "emails_sent": len(emails_sent),
        "payments": len(payments),
        "failures": len(failures),
        "failure_rate": round(len(failures) / max(len(entries), 1) * 100, 1),
        "recent_failures": failures[-10:],
    }
