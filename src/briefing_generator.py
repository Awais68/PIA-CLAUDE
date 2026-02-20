"""CEO Briefing Generator for Zoya — Gold Tier G1.

Generates daily or weekly briefing documents in AI_Employee_Vault/Briefings/.
Aggregates data from all vault folders and channels.

Usage:
    uv run zoya-briefing [--weekly]
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import (
    APPROVED,
    BRIEFINGS,
    DONE,
    HANDBOOK,
    IN_PROGRESS,
    INBOX,
    NEEDS_ACTION,
    PENDING_APPROVAL,
    PLANS,
    QUARANTINE,
    REJECTED,
    VAULT_PATH,
)

BUSINESS_GOALS = VAULT_PATH / "Business_Goals.md"
from src.utils import log_action, setup_logger

logger = setup_logger("briefing_generator")

# ---------------------------------------------------------------------------
# Frontmatter reader (local copy — avoids importing orchestrator)
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


# ---------------------------------------------------------------------------
# Data collection helpers
# ---------------------------------------------------------------------------

def _count(folder: Path) -> int:
    """Count non-gitkeep files in a folder."""
    if not folder.exists():
        return 0
    return len([f for f in folder.iterdir() if f.is_file() and f.name != ".gitkeep"])


def _collect_done_in_period(since: datetime) -> list[dict]:
    """Collect Done/ items processed within the briefing period."""
    if not DONE.exists():
        return []
    items = []
    for f in DONE.glob("FILE_*.md"):
        fm = _read_frontmatter(f)
        processed_at_str = fm.get("processed_at", "")
        if not processed_at_str:
            continue
        try:
            # Parse ISO timestamp (strip timezone if needed)
            processed_at = datetime.fromisoformat(processed_at_str.replace("Z", "+00:00"))
            if processed_at.tzinfo is None:
                processed_at = processed_at.replace(tzinfo=timezone.utc)
            if processed_at >= since:
                items.append({
                    "name": fm.get("original_name", f.name),
                    "type": fm.get("type", "other"),
                    "source": fm.get("source", "file_drop"),
                    "priority": fm.get("priority", "low"),
                    "processed_at": processed_at_str[:19],
                    "approval_status": fm.get("approval_status", "auto"),
                })
        except (ValueError, TypeError):
            continue
    return sorted(items, key=lambda x: x["processed_at"], reverse=True)


def _collect_pending() -> list[dict]:
    """Collect items currently waiting in Needs_Action."""
    if not NEEDS_ACTION.exists():
        return []
    items = []
    for f in NEEDS_ACTION.glob("FILE_*.md"):
        fm = _read_frontmatter(f)
        if fm.get("status") == "pending":
            items.append({
                "name": fm.get("original_name", f.name),
                "type": fm.get("type", "other"),
                "source": fm.get("source", "file_drop"),
                "priority": fm.get("priority", "low"),
                "queued_at": fm.get("queued_at", ""),
            })
    return items


def _collect_pending_approval() -> list[dict]:
    """Collect items in Pending_Approval/ awaiting human review."""
    if not PENDING_APPROVAL.exists():
        return []
    items = []
    for f in PENDING_APPROVAL.glob("*.md"):
        fm = _read_frontmatter(f)
        items.append({
            "name": fm.get("original_name", f.name),
            "type": fm.get("type", "other"),
            "source": fm.get("source", "file_drop"),
            "requested_at": fm.get("approval_requested_at", ""),
        })
    return items


def _collect_quarantine() -> list[dict]:
    """Collect items in Quarantine/ needing manual review."""
    if not QUARANTINE.exists():
        return []
    items = []
    for f in QUARANTINE.glob("*.md"):
        if f.name.endswith(".reason.md"):
            continue
        fm = _read_frontmatter(f)
        items.append({
            "name": fm.get("original_name", f.name),
            "reason": fm.get("reason", "unknown"),
            "retries": fm.get("retry_count", "0"),
        })
    return items


def _extract_deadlines_from_done(since: datetime) -> list[str]:
    """Scan recently-done items for action items with deadlines."""
    deadlines = []
    if not DONE.exists():
        return deadlines
    for f in sorted(DONE.glob("FILE_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
        try:
            text = f.read_text(encoding="utf-8")
            # Look for action items with dates
            matches = re.findall(
                r"- \[ \] .{0,80}(?:by|due|deadline|before)\s+\S+",
                text,
                re.IGNORECASE,
            )
            deadlines.extend(matches[:3])  # max 3 per file
        except OSError:
            continue
    return deadlines[:10]  # max 10 total


def _read_business_goals() -> dict:
    """Read Business_Goals.md and extract revenue target and key metrics."""
    if not BUSINESS_GOALS.exists():
        return {}
    try:
        text = BUSINESS_GOALS.read_text(encoding="utf-8")
    except OSError:
        return {}

    goals: dict = {}
    # Monthly goal
    goal_match = re.search(r"Monthly goal:\s*\$?([\d,]+)", text)
    if goal_match:
        goals["monthly_goal"] = float(goal_match.group(1).replace(",", ""))
    # Current MTD
    mtd_match = re.search(r"Current MTD:\s*\$?([\d,]+)", text)
    if mtd_match:
        goals["current_mtd"] = float(mtd_match.group(1).replace(",", ""))
    return goals


def _extract_revenue_from_done(since: datetime) -> dict:
    """Scan Done/ items for invoice/receipt amounts in the given period.

    Returns dict with total_revenue (float) and invoices (list of dicts).
    """
    if not DONE.exists():
        return {"total_revenue": 0.0, "invoices": [], "paid_count": 0, "unpaid_count": 0}

    total = 0.0
    invoices = []
    paid_count = 0
    unpaid_count = 0

    for f in DONE.glob("FILE_*.md"):
        fm = _read_frontmatter(f)
        doc_type = fm.get("type", "")
        if doc_type not in ("invoice", "receipt"):
            continue
        processed_at_str = fm.get("processed_at", "")
        if not processed_at_str:
            continue
        try:
            processed_at = datetime.fromisoformat(processed_at_str.replace("Z", "+00:00"))
            if processed_at.tzinfo is None:
                processed_at = processed_at.replace(tzinfo=timezone.utc)
            if processed_at < since:
                continue
        except (ValueError, TypeError):
            continue

        # Try to extract amount from body
        try:
            body = f.read_text(encoding="utf-8")
        except OSError:
            body = ""
        amt_match = re.search(
            r"(?:amount|total|invoice\s+total|due)[:\s]+\$?([\d,]+(?:\.\d{2})?)",
            body, re.IGNORECASE,
        )
        amount = float(amt_match.group(1).replace(",", "")) if amt_match else 0.0
        total += amount

        payment_state = fm.get("payment_state", fm.get("payment_status", ""))
        is_paid = payment_state in ("paid", "in_payment", "approved")
        if is_paid:
            paid_count += 1
        else:
            unpaid_count += 1

        invoices.append({
            "name": fm.get("original_name", f.name),
            "amount": amount,
            "paid": is_paid,
            "date": processed_at_str[:10],
        })

    return {
        "total_revenue": total,
        "invoices": sorted(invoices, key=lambda x: x["date"], reverse=True),
        "paid_count": paid_count,
        "unpaid_count": unpaid_count,
    }


def _source_breakdown(items: list[dict]) -> dict[str, int]:
    """Count items by source channel."""
    counts: dict[str, int] = {"file_drop": 0, "gmail": 0, "whatsapp": 0}
    for item in items:
        src = item.get("source", "file_drop")
        counts[src] = counts.get(src, 0) + 1
    return counts


def _type_breakdown(items: list[dict]) -> dict[str, int]:
    """Count items by document type."""
    counts: dict[str, int] = {}
    for item in items:
        t = item.get("type", "other")
        counts[t] = counts.get(t, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Briefing writer
# ---------------------------------------------------------------------------

def generate_briefing(period: str = "daily") -> Path:
    """Generate a briefing document for the specified period.

    Args:
        period: "daily" (last 24h) or "weekly" (last 7d).

    Returns:
        Path to the generated briefing file.
    """
    BRIEFINGS.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    if period == "weekly":
        since = now - timedelta(days=7)
        period_label = "Weekly"
    else:
        since = now - timedelta(days=1)
        period_label = "Daily"

    # Collect data
    done_items = _collect_done_in_period(since)
    pending_items = _collect_pending()
    approval_items = _collect_pending_approval()
    quarantine_items = _collect_quarantine()
    deadlines = _extract_deadlines_from_done(since)
    revenue_data = _extract_revenue_from_done(since)
    business_goals = _read_business_goals()

    # Current queue counts
    queue_counts = {
        "Inbox": _count(INBOX),
        "Needs_Action": _count(NEEDS_ACTION),
        "In_Progress": _count(IN_PROGRESS),
        "Done": _count(DONE),
        "Quarantine": _count(QUARANTINE),
        "Pending_Approval": _count(PENDING_APPROVAL),
        "Plans": _count(PLANS),
        "Approved": _count(APPROVED),
        "Rejected": _count(REJECTED),
        "Briefings": _count(BRIEFINGS),
    }

    # Build source breakdown for processed items
    src_counts = _source_breakdown(done_items)
    type_counts = _type_breakdown(done_items)

    # Completed items table
    completed_rows = "\n".join(
        f"| {i['name'][:40]} | {i['type']} | {i['source']} | "
        f"{i['priority']} | {i.get('approval_status','auto')} | {i['processed_at'][:16]} |"
        for i in done_items[:15]
    ) or "| No items completed in this period | | | | | |"

    # Pending items table
    pending_rows = "\n".join(
        f"| {i['name'][:40]} | {i['type']} | {i['source']} | {i['priority']} | {i['queued_at'][:16]} |"
        for i in pending_items[:10]
    ) or "| No pending items | | | | |"

    # Awaiting approval table
    approval_rows = "\n".join(
        f"| {i['name'][:40]} | {i['type']} | {i['source']} | {i['requested_at'][:16]} |"
        for i in approval_items[:10]
    ) or "| No items awaiting approval | | | |"

    # Quarantine alerts
    quarantine_section = ""
    if quarantine_items:
        q_lines = "\n".join(
            f"- **{i['name']}** — {i['reason']} (retried {i['retries']}x)"
            for i in quarantine_items
        )
        quarantine_section = f"\n## ⚠️ Attention Required\n\n{q_lines}\n"

    # Deadlines section
    deadline_section = ""
    if deadlines:
        d_lines = "\n".join(f"- {d}" for d in deadlines)
        deadline_section = f"\n## Upcoming Deadlines\n\n{d_lines}\n"

    # Weekly trend note
    trend_section = ""
    if period == "weekly":
        total_done_ever = _count(DONE)
        avg_per_day = len(done_items) / 7 if done_items else 0
        trend_section = (
            f"\n## Weekly Trends\n\n"
            f"- Items processed this week: {len(done_items)}\n"
            f"- Daily average: {avg_per_day:.1f}\n"
            f"- Total archived in Done/: {total_done_ever}\n"
        )

    # System health score (0-100)
    health_score = _compute_health_score(queue_counts, quarantine_items, approval_items)

    # Revenue section
    monthly_goal = business_goals.get("monthly_goal", 0)
    current_mtd = business_goals.get("current_mtd", 0) + revenue_data["total_revenue"]
    pct_of_goal = (current_mtd / monthly_goal * 100) if monthly_goal > 0 else 0
    revenue_trend = "On track" if pct_of_goal >= 40 else "Behind target"

    revenue_section = (
        f"\n## Revenue\n\n"
        f"| Metric | Value |\n|--------|-------|\n"
        f"| Period revenue | ${revenue_data['total_revenue']:,.2f} |\n"
        f"| MTD total | ${current_mtd:,.2f} |\n"
        f"| Monthly goal | ${monthly_goal:,.2f} |\n"
        f"| Goal progress | {pct_of_goal:.0f}% |\n"
        f"| Trend | {revenue_trend} |\n"
        f"| Paid invoices | {revenue_data['paid_count']} |\n"
        f"| Unpaid invoices | {revenue_data['unpaid_count']} |\n"
    )
    if revenue_data["invoices"]:
        inv_rows = "\n".join(
            f"| {i['name'][:40]} | ${i['amount']:,.2f} | {'✓ Paid' if i['paid'] else '⏳ Pending'} | {i['date']} |"
            for i in revenue_data["invoices"][:5]
        )
        revenue_section += (
            f"\n**Recent Invoices:**\n\n"
            f"| File | Amount | Status | Date |\n"
            f"|------|--------|--------|------|\n"
            f"{inv_rows}\n"
        )

    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M UTC")
    briefing_name = f"BRIEFING_{now.strftime('%Y%m%d_%H%M%S')}_{period}.md"
    briefing_path = BRIEFINGS / briefing_name

    content = (
        f"---\n"
        f"type: briefing\n"
        f"period: {period}\n"
        f"generated_at: {now.isoformat()}\n"
        f"covers_from: {since.isoformat()}\n"
        f"covers_to: {now.isoformat()}\n"
        f"health_score: {health_score}\n"
        f"revenue_period: {revenue_data['total_revenue']:.2f}\n"
        f"revenue_mtd: {current_mtd:.2f}\n"
        f"---\n\n"
        f"# {period_label} Briefing — {date_str}\n\n"
        f"**Generated:** {date_str} at {time_str}  \n"
        f"**Period:** Last {'24 hours' if period == 'daily' else '7 days'}  \n"
        f"**System Health:** {health_score}/100\n"
        f"{revenue_section}\n"
        f"## Summary\n\n"
        f"| Metric | Count |\n|--------|-------|\n"
        f"| Processed in period | {len(done_items)} |\n"
        f"| Pending in queue | {len(pending_items)} |\n"
        f"| Awaiting approval | {len(approval_items)} |\n"
        f"| In quarantine | {len(quarantine_items)} |\n"
        f"| Total in Done/ | {queue_counts['Done']} |\n\n"
        f"## Channel Breakdown\n\n"
        f"| Channel | Processed |\n|---------|----------|\n"
        f"| File Drop | {src_counts.get('file_drop', 0)} |\n"
        f"| Gmail | {src_counts.get('gmail', 0)} |\n"
        f"| WhatsApp | {src_counts.get('whatsapp', 0)} |\n\n"
        f"## Document Types\n\n"
        f"| Type | Count |\n|------|-------|\n"
        + "\n".join(f"| {t} | {c} |" for t, c in sorted(type_counts.items(), key=lambda x: -x[1]))
        + ("\n| (none) | 0 |" if not type_counts else "")
        + f"\n\n"
        f"## Completed Items\n\n"
        f"| File | Type | Channel | Priority | Approval | Processed |\n"
        f"|------|------|---------|----------|----------|-----------|\n"
        f"{completed_rows}\n"
        f"\n## Pending Items\n\n"
        f"| File | Type | Channel | Priority | Queued |\n"
        f"|------|------|---------|----------|--------|\n"
        f"{pending_rows}\n"
        f"\n## Awaiting Human Approval\n\n"
        f"| File | Type | Channel | Requested |\n"
        f"|------|------|---------|----------|\n"
        f"{approval_rows}\n"
        f"{quarantine_section}"
        f"{deadline_section}"
        f"{trend_section}"
        f"\n---\n*Generated by Zoya AI Employee — {period_label} Briefing System*\n"
    )

    briefing_path.write_text(content, encoding="utf-8")
    log_action("briefing_generated", str(briefing_path), {"period": period, "health_score": health_score})
    logger.info("Briefing generated: %s (health=%d)", briefing_name, health_score)
    return briefing_path


def _compute_health_score(
    queue_counts: dict[str, int],
    quarantine_items: list[dict],
    approval_items: list[dict],
) -> int:
    """Compute a 0-100 system health score.

    Penalties:
    - Each quarantined item: -10
    - Each item stuck in In_Progress (>0 signals possible stuck): -5
    - Large pending queue (>10): -5
    - Large approval backlog (>5): -5
    """
    score = 100
    score -= len(quarantine_items) * 10
    score -= queue_counts.get("In_Progress", 0) * 5
    if queue_counts.get("Needs_Action", 0) > 10:
        score -= 5
    if len(approval_items) > 5:
        score -= 5
    return max(0, min(100, score))


def get_latest_briefing(period: str = "daily") -> Path | None:
    """Return the most recent briefing file for the given period."""
    if not BRIEFINGS.exists():
        return None
    matches = sorted(BRIEFINGS.glob(f"BRIEFING_*_{period}.md"), reverse=True)
    return matches[0] if matches else None


def list_briefings() -> list[Path]:
    """Return all briefing files sorted newest first."""
    if not BRIEFINGS.exists():
        return []
    return sorted(BRIEFINGS.glob("BRIEFING_*.md"), reverse=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate a briefing and print its path."""
    import argparse

    parser = argparse.ArgumentParser(description="Zoya CEO Briefing Generator")
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="Generate weekly briefing instead of daily",
    )
    args = parser.parse_args()

    period = "weekly" if args.weekly else "daily"
    briefing_path = generate_briefing(period)
    print(f"Briefing generated: {briefing_path}")


if __name__ == "__main__":
    main()
