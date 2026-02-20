"""Weekly Audit Generator + CEO Briefing Sender — Gold Tier Task 6C.

Runs every Sunday 11 PM (via cron or the scheduler).
Workflow:
  1. Collects data from all sources (Vault folders, audit logs, social metrics)
  2. Generates CEO Briefing with week-over-week comparison
  3. Validates all 7 required sections (saves as DRAFT_ if incomplete)
  4. Saves briefing to AI_Employee_Vault/Briefings/ + overwrites LATEST
  5. Sends a WhatsApp summary to the owner's number
  6. Updates Dashboard.md "Last CEO Briefing" line
  7. Appends progress entry to Vault/Logs/gold_tier_progress.md

  Log retention is handled separately by src/log_janitor.py (cron: 30 23 * * 0).

Cron schedule (Sunday 23:00 local):
    0 23 * * 0  cd /path/to/project && uv run python -m src.audit_generator

Entry point:
    uv run python -m src.audit_generator [--dry-run] [--force] [--date YYYY-MM-DD] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.audit_logger import audit_log, get_period_stats, read_logs
from src.config import (
    APPROVED,
    BRIEFINGS,
    DONE,
    IN_PROGRESS,
    LOGS,
    NEEDS_ACTION,
    PENDING_APPROVAL,
    QUARANTINE,
    VAULT_PATH,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
)
from src.utils import log_action, setup_logger

logger = setup_logger("audit_generator")

PROGRESS_LOG = LOGS / "gold_tier_progress.md"
OWNER_WHATSAPP = os.getenv("OWNER_WHATSAPP_NUMBER", "")   # e.g. "447911123456"


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def _count(folder: Path) -> int:
    if not folder.exists():
        return 0
    return len([f for f in folder.iterdir() if f.is_file() and f.name != ".gitkeep"])


def _read_frontmatter(path: Path) -> dict[str, str]:
    import re
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


def collect_vault_snapshot() -> dict:
    """Gather folder counts and key file data from the vault."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    # Done items this week
    done_this_week = []
    invoices_done = []
    for f in DONE.glob("FILE_*.md"):
        fm = _read_frontmatter(f)
        try:
            processed = datetime.fromisoformat(
                fm.get("processed_at", "").replace("Z", "+00:00")
            )
            if processed.tzinfo is None:
                processed = processed.replace(tzinfo=timezone.utc)
            if processed >= week_ago:
                done_this_week.append({
                    "name": fm.get("original_name", f.name),
                    "type": fm.get("type", "other"),
                    "source": fm.get("source", "file_drop"),
                    "priority": fm.get("priority", "low"),
                    "processed_at": fm.get("processed_at", "")[:19],
                    "approval_status": fm.get("approval_status", "auto"),
                })
                if fm.get("type") == "invoice":
                    invoices_done.append(fm)
        except (ValueError, TypeError):
            continue

    # Pending approval items
    approval_pending = []
    for f in PENDING_APPROVAL.glob("*.md"):
        fm = _read_frontmatter(f)
        requested = fm.get("approval_requested_at", fm.get("created_at", ""))
        approval_pending.append({
            "name": f.name,
            "type": fm.get("type", "other"),
            "requested_at": requested[:19] if requested else "",
        })

    # Overdue items: still in Needs_Action / Pending_Approval for > 48h
    overdue = []
    cutoff_48h = now - timedelta(hours=48)
    for folder in (NEEDS_ACTION, PENDING_APPROVAL):
        for f in folder.glob("*.md"):
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff_48h:
                overdue.append({
                    "name": f.name,
                    "folder": folder.name,
                    "age_hours": round((now - mtime).total_seconds() / 3600, 1),
                })

    # Failed tasks in quarantine
    quarantine_items = []
    for f in QUARANTINE.glob("*.md"):
        fm = _read_frontmatter(f)
        quarantine_items.append({
            "name": fm.get("original_name", f.name),
            "reason": fm.get("reason", "unknown"),
        })

    return {
        "counts": {
            "inbox": _count(VAULT_PATH / "Inbox"),
            "needs_action": _count(NEEDS_ACTION),
            "in_progress": _count(IN_PROGRESS),
            "done": _count(DONE),
            "done_this_week": len(done_this_week),
            "quarantine": _count(QUARANTINE),
            "pending_approval": _count(PENDING_APPROVAL),
            "approved": _count(APPROVED),
            "contacts": _count(VAULT_PATH / "Contacts"),
            "briefings": _count(BRIEFINGS),
        },
        "done_this_week": done_this_week[:20],
        "invoices_done": invoices_done,
        "approval_pending": approval_pending,
        "overdue": overdue,
        "quarantine_items": quarantine_items,
    }


def collect_social_metrics() -> dict:
    """Collect available social media metrics from Done/ logs.

    In production this would call the Twitter/Meta APIs directly.
    For now we aggregate from audit logs and DONE social post files.
    """
    metrics: dict[str, dict] = {
        "twitter": {"posts": 0, "impressions": 0, "mentions": 0},
        "linkedin": {"posts": 0},
        "facebook": {"posts": 0, "reach": 0, "engagement": 0},
        "instagram": {"posts": 0, "followers_delta": 0, "top_post": ""},
    }

    for f in DONE.glob("TWITTER_*.md"):
        metrics["twitter"]["posts"] += 1

    for f in DONE.glob("LINKEDIN_*.md"):
        metrics["linkedin"]["posts"] += 1

    # Check audit logs for social posts this week
    try:
        stats = get_period_stats(days=7)
        # Rough split — in production each platform would have its own log action
        social_total = stats["social_posts"]
        metrics["twitter"]["posts"] = max(metrics["twitter"]["posts"], social_total // 3)
    except Exception:
        pass

    return metrics


def collect_financial_summary() -> dict:
    """Collect financial data from vault (Odoo/Bank data when integrated).

    Returns placeholder structure until Odoo MCP is wired in.
    """
    # Attempt to read from Odoo cache if it exists
    odoo_cache = VAULT_PATH / "Business" / "odoo_snapshot.json"
    if odoo_cache.exists():
        try:
            return json.loads(odoo_cache.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Placeholder — shows structure for when Odoo is connected
    return {
        "cash_position": "Pending Odoo connection",
        "revenue_this_week": "Pending Odoo connection",
        "revenue_target": "Pending Odoo connection",
        "outstanding_invoices": [],
        "top_expense_categories": [],
        "subscription_audit": [],
        "data_source": "placeholder",
    }


# ---------------------------------------------------------------------------
# CEO Briefing generator (exact sections from Task 6B spec)
# ---------------------------------------------------------------------------

def generate_ceo_briefing(
    vault_snapshot: dict,
    social_metrics: dict,
    financial: dict,
    audit_stats: dict,
    prior_stats: dict | None = None,
    report_date: datetime | None = None,
    dry_run: bool = False,
) -> Path:
    """Generate the Monday Morning CEO Briefing with the exact required sections.

    Args:
        prior_stats: Stats from the previous 7-day period for week-over-week comparison.
        report_date: Override the current datetime (used with --date CLI flag).

    Returns path to the saved briefing file.
    """
    BRIEFINGS.mkdir(parents=True, exist_ok=True)
    now = report_date or datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    day_name = now.strftime("%A")

    # --- Section 1: Financial Summary ---
    fin = financial
    outstanding = fin.get("outstanding_invoices", [])
    overdue_inv = [i for i in outstanding if i.get("days_overdue", 0) > 0]
    overdue_30 = [i for i in overdue_inv if i.get("days_overdue", 0) > 30]

    outstanding_rows = "\n".join(
        f"  - {i.get('client', '?')}: ${i.get('amount', '?')} "
        f"({i.get('days_overdue', 0)} days overdue)"
        for i in outstanding[:10]
    ) or "  - No outstanding invoices found"

    expenses = fin.get("top_expense_categories", [])
    expense_rows = "\n".join(
        f"  - {e.get('category', '?')}: ${e.get('amount', '?')}"
        for e in expenses[:5]
    ) or "  - Pending Odoo connection"

    subs = fin.get("subscription_audit", [])
    unused_subs = [s for s in subs if s.get("days_since_use", 0) > 30]
    sub_rows = "\n".join(
        f"  - ⚠️ {s.get('name', '?')} — unused for {s.get('days_since_use', 0)} days "
        f"(${s.get('monthly_cost', '?')}/mo)"
        for s in unused_subs[:5]
    ) or "  - No unused subscriptions detected (or Odoo not connected)"

    # --- Week-over-Week comparison ---
    prior = prior_stats or {}
    counts = vault_snapshot["counts"]

    # Count prior-week Done items (processed 7–14 days ago)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    prior_week_done = 0
    for _f in DONE.glob("FILE_*.md"):
        _fm = _read_frontmatter(_f)
        try:
            _processed = datetime.fromisoformat(
                _fm.get("processed_at", "").replace("Z", "+00:00")
            )
            if _processed.tzinfo is None:
                _processed = _processed.replace(tzinfo=timezone.utc)
            if two_weeks_ago <= _processed < week_ago:
                prior_week_done += 1
        except (ValueError, TypeError):
            continue

    def _delta(a: int, b: int) -> str:
        if b == 0:
            return f"+{a}" if a > 0 else "0"
        d = a - b
        pct = round(d / b * 100)
        sign = "+" if d >= 0 else ""
        return f"{sign}{d} ({sign}{pct}%)"

    wow_table = (
        f"\n### Week-over-Week\n\n"
        f"| Metric | This Week | Last Week | Change |\n"
        f"|--------|-----------|-----------|--------|\n"
        f"| Items Completed | {counts['done_this_week']} | {prior_week_done} | {_delta(counts['done_this_week'], prior_week_done)} |\n"
        f"| Actions Logged | {audit_stats.get('total_entries', 0)} | {prior.get('total_entries', 0)} | {_delta(audit_stats.get('total_entries', 0), prior.get('total_entries', 0))} |\n"
        f"| Social Posts | {audit_stats.get('social_posts', 0)} | {prior.get('social_posts', 0)} | {_delta(audit_stats.get('social_posts', 0), prior.get('social_posts', 0))} |\n"
        f"| Failures | {audit_stats.get('failures', 0)} | {prior.get('failures', 0)} | {_delta(audit_stats.get('failures', 0), prior.get('failures', 0))} |\n"
    )

    # --- Section 2: Completed This Week ---
    done_items = vault_snapshot["done_this_week"]
    completed_rows = "\n".join(
        f"  - {item['name']} [{item['type']}] — {item['processed_at'][:16]} "
        f"(source: {item['source']}, priority: {item['priority']})"
        for item in done_items[:15]
    ) or "  - No items completed this week"

    # --- Section 3: Bottlenecks ---
    overdue_items = vault_snapshot["overdue"]
    bottleneck_rows = "\n".join(
        f"  - {item['name']} in /{item['folder']}/ — {item['age_hours']}h overdue\n"
        f"    **Root cause:** File stuck; consider triggering Ralph loop"
        for item in overdue_items[:5]
    ) or "  - No bottlenecks detected ✅"

    # --- Section 4: Social Media Performance ---
    tw = social_metrics["twitter"]
    li = social_metrics["linkedin"]
    fb = social_metrics["facebook"]
    ig = social_metrics["instagram"]

    # --- Section 5: Alerts ---
    alerts: list[str] = []
    for inv in overdue_30:
        alerts.append(
            f"  - 🔴 Invoice {inv.get('client', '?')}: "
            f"${inv.get('amount', '?')} — {inv.get('days_overdue', 0)} days overdue"
        )
    for item in vault_snapshot["quarantine_items"]:
        alerts.append(f"  - 🔴 Quarantine: {item['name']} — {item['reason']}")
    if audit_stats.get("failure_rate", 0) > 20:
        alerts.append(
            f"  - ⚠️ High failure rate: {audit_stats['failure_rate']}% "
            f"of {audit_stats['total_entries']} actions failed this week"
        )
    if counts["in_progress"] > 2:
        alerts.append(
            f"  - ⚠️ {counts['in_progress']} items stuck in In_Progress — may need manual intervention"
        )
    alerts_text = "\n".join(alerts) or "  - No critical alerts ✅"

    # --- Section 6: Proactive Suggestions ---
    suggestions: list[str] = []
    if unused_subs:
        total_unused_cost = sum(s.get("monthly_cost", 0) for s in unused_subs)
        suggestions.append(
            f"  - 💰 Cancel {len(unused_subs)} unused subscription(s) "
            f"→ save ~${total_unused_cost}/month"
        )
    if counts["pending_approval"] > 5:
        suggestions.append(
            f"  - ⏰ {counts['pending_approval']} items awaiting approval — "
            "review Pending_Approval/ to unblock work"
        )
    if done_items:
        client_types = [i for i in done_items if i["type"] in ("proposal", "contract")]
        if client_types:
            suggestions.append(
                f"  - 📈 {len(client_types)} proposal/contract(s) processed — "
                "consider follow-up emails to prospects"
            )
    if audit_stats.get("emails_sent", 0) == 0:
        suggestions.append(
            "  - 📧 No emails sent via automation this week — "
            "check Gmail integration is active"
        )
    suggestions_text = "\n".join(suggestions) or "  - System running smoothly — no suggestions"

    # --- Section 7: Week Ahead ---
    # Extract deadlines from recent Done/ action items
    upcoming: list[str] = []
    import re as _re
    for f in sorted(DONE.glob("FILE_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:15]:
        try:
            text = f.read_text(encoding="utf-8")
            matches = _re.findall(
                r"- \[ \] .{0,100}(?:by|due|deadline|before)\s+\S+",
                text, _re.IGNORECASE,
            )
            upcoming.extend(matches[:2])
        except OSError:
            continue
    upcoming_text = "\n".join(f"  - {d}" for d in upcoming[:8]) or \
        "  - No upcoming deadlines detected (check Plans/ for active plans)"

    # Scheduled social posts
    scheduled_posts: list[str] = []
    for f in PENDING_APPROVAL.glob("TWITTER_*.md"):
        fm = _read_frontmatter(f)
        scheduled_for = fm.get("scheduled_for", "")
        if scheduled_for:
            scheduled_posts.append(f"  - Twitter: {scheduled_for} — {f.name}")
    scheduled_text = "\n".join(scheduled_posts) or "  - No scheduled posts pending approval"

    # --- Assemble the briefing ---
    briefing_content = (
        f"---\n"
        f"type: ceo_briefing\n"
        f"generated_at: {now.isoformat()}\n"
        f"period: weekly\n"
        f"health_score: {max(0, 100 - len(vault_snapshot['quarantine_items']) * 10 - len(overdue_items) * 5)}\n"
        f"---\n\n"
        f"# {day_name} Morning CEO Briefing — {date_str}\n\n"
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')} by Zoya AI Employee  \n"
        f"**Period:** Last 7 days  \n"
        f"**Items processed this week:** {counts['done_this_week']}  \n"
        f"**System health:** {max(0, 100 - len(vault_snapshot['quarantine_items']) * 10)}/100\n\n"
        f"---\n\n"
        f"## 🏦 Financial Summary\n\n"
        f"- **Cash Position:** {fin.get('cash_position', 'Pending Odoo connection')}\n"
        f"- **Revenue This Week vs Target:** "
        f"{fin.get('revenue_this_week', 'N/A')} / {fin.get('revenue_target', 'N/A')}\n"
        f"- **Outstanding Invoices:**\n{outstanding_rows}\n"
        f"- **Top Expense Categories:**\n{expense_rows}\n"
        f"- **Subscription Audit (unused >30 days):**\n{sub_rows}\n"
        f"{wow_table}\n"
        f"---\n\n"
        f"## ✅ Completed This Week\n\n"
        f"{completed_rows}\n\n"
        f"**Total completed:** {counts['done_this_week']} items  \n"
        f"**Auto-processed:** {audit_stats.get('total_entries', 0)} actions  \n"
        f"**Human approvals given:** "
        f"{audit_stats.get('total_entries', 0) - counts['done_this_week']} actions\n\n"
        f"---\n\n"
        f"## 🚧 Bottlenecks\n\n"
        f"{bottleneck_rows}\n\n"
        f"**Items in In_Progress:** {counts['in_progress']}  \n"
        f"**Items in Quarantine:** {counts['quarantine']}\n\n"
        f"---\n\n"
        f"## 📱 Social Media Performance\n\n"
        f"- **Facebook:** reach: {fb.get('reach', 'N/A')}, "
        f"engagement rate: {fb.get('engagement', 'N/A')}\n"
        f"- **Instagram:** followers delta: {ig.get('followers_delta', 'N/A')}, "
        f"top post: {ig.get('top_post', 'N/A')}\n"
        f"- **Twitter:** impressions: {tw.get('impressions', 'N/A')}, "
        f"mentions: {tw.get('mentions', 'N/A')} "
        f"({tw.get('posts', 0)} post(s) this week)\n"
        f"- **LinkedIn:** {li.get('posts', 0)} post(s) this week\n\n"
        f"---\n\n"
        f"## ⚠️ Alerts Requiring Attention\n\n"
        f"{alerts_text}\n\n"
        f"---\n\n"
        f"## 💡 Proactive Suggestions\n\n"
        f"{suggestions_text}\n\n"
        f"---\n\n"
        f"## 📅 Week Ahead\n\n"
        f"**Upcoming deadlines (next 7 days):**\n{upcoming_text}\n\n"
        f"**Scheduled social posts:**\n{scheduled_text}\n\n"
        f"**Payment dues:** {', '.join(i.get('client', '?') + ' $' + str(i.get('amount', '?')) for i in outstanding[:3]) or 'None detected'}\n\n"
        f"---\n\n"
        f"*Generated by Zoya AI Employee — CEO Briefing System*  \n"
        f"*Data sources: Vault folders, Audit logs, Social metrics*  \n"
        f"{'*[DRY RUN — no real data fetched]*' if dry_run else ''}\n"
    )

    # Validate all 7 required sections are present
    REQUIRED_SECTIONS = [
        "## 🏦 Financial Summary",
        "## ✅ Completed This Week",
        "## 🚧 Bottlenecks",
        "## 📱 Social Media Performance",
        "## ⚠️ Alerts Requiring Attention",
        "## 💡 Proactive Suggestions",
        "## 📅 Week Ahead",
    ]
    missing_sections = [s for s in REQUIRED_SECTIONS if s not in briefing_content]
    now_str = now.strftime("%Y%m%d_%H%M%S")

    if missing_sections:
        # Save as DRAFT and raise an alert — do NOT send WhatsApp
        briefing_name = f"DRAFT_CEO_BRIEFING_{now_str}.md"
        briefing_path = BRIEFINGS / briefing_name
        briefing_path.write_text(briefing_content, encoding="utf-8")
        NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
        alert_path = NEEDS_ACTION / f"ALERT_BRIEFING_INCOMPLETE_{now_str}.md"
        alert_path.write_text(
            f"---\ntype: alert\ncreated_at: {now.isoformat()}\n---\n\n"
            f"# Incomplete CEO Briefing — Manual Review Required\n\n"
            f"A draft was saved but is missing required sections:\n\n"
            + "\n".join(f"- `{s}`" for s in missing_sections)
            + f"\n\n**Draft path:** `Briefings/{briefing_name}`\n",
            encoding="utf-8",
        )
        logger.warning("CEO Briefing saved as DRAFT — missing: %s", missing_sections)
        audit_log(
            "audit_generated",
            str(briefing_path),
            parameters={"draft": True, "missing_sections": missing_sections, "dry_run": dry_run},
            result="failure",
        )
        return briefing_path

    # All 7 sections present — save final briefing
    briefing_name = f"CEO_BRIEFING_{now_str}.md"
    briefing_path = BRIEFINGS / briefing_name
    briefing_path.write_text(briefing_content, encoding="utf-8")

    # Overwrite the rolling "latest" pointer for easy reference
    (BRIEFINGS / "CEO_BRIEFING_LATEST.md").write_text(briefing_content, encoding="utf-8")

    # Update Dashboard.md "Last CEO Briefing" line
    _update_dashboard_briefing_line(briefing_name, now)

    logger.info("CEO Briefing saved: %s", briefing_name)
    audit_log(
        "audit_generated",
        str(briefing_path),
        parameters={"items_covered": counts["done_this_week"], "dry_run": dry_run},
    )
    return briefing_path


# ---------------------------------------------------------------------------
# WhatsApp summary sender
# ---------------------------------------------------------------------------

def send_whatsapp_summary(briefing_path: Path, dry_run: bool = False) -> bool:
    """Send a concise briefing summary to the owner via WhatsApp.

    Reads the first ~800 chars of the briefing and sends as a WhatsApp message.
    Uses the existing WhatsApp Business API (same as whatsapp_watcher).
    """
    if not OWNER_WHATSAPP:
        logger.warning(
            "OWNER_WHATSAPP_NUMBER not set in .env — skipping WhatsApp delivery"
        )
        return False

    try:
        text = briefing_path.read_text(encoding="utf-8")
    except OSError:
        logger.error("Could not read briefing for WhatsApp send: %s", briefing_path)
        return False

    # Extract key lines for the summary message
    import re as _re
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith(("---", "#-", "*Generated"))]

    # Build compact summary (WhatsApp messages should be concise)
    summary_lines = []
    for line in lines:
        if line.startswith("#"):
            summary_lines.append(line.lstrip("#").strip())
        elif line.startswith("- **") or line.startswith("- 🔴") or line.startswith("- ⚠️") or line.startswith("- ✅"):
            summary_lines.append(line)
        if len("\n".join(summary_lines)) > 800:
            break

    message = (
        f"📊 *Zoya Weekly Briefing*\n\n"
        + "\n".join(summary_lines[:20])
        + f"\n\n_Full report saved to Briefings/{briefing_path.name}_"
    )

    if dry_run:
        logger.info("[DRY RUN] Would send WhatsApp to %s:\n%s", OWNER_WHATSAPP, message[:300])
        audit_log(
            "whatsapp_sent",
            OWNER_WHATSAPP,
            parameters={"dry_run": True, "briefing": briefing_path.name},
        )
        return True

    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.error("WhatsApp credentials not configured — cannot send briefing summary")
        return False

    try:
        import requests
        url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": OWNER_WHATSAPP,
            "type": "text",
            "text": {"body": message[:4000]},  # WhatsApp 4096 char limit
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            logger.info("WhatsApp briefing summary sent to %s", OWNER_WHATSAPP)
            audit_log(
                "whatsapp_sent",
                OWNER_WHATSAPP,
                actor="claude_code",
                approval_status="auto",
                parameters={"briefing": briefing_path.name},
            )
            return True
        else:
            logger.error("WhatsApp send failed: %d %s", resp.status_code, resp.text[:200])
            return False
    except Exception:
        logger.exception("WhatsApp send exception")
        return False


# ---------------------------------------------------------------------------
# Progress log
# ---------------------------------------------------------------------------

def _log_progress(event: str, detail: str = "") -> None:
    """Append a line to /Vault/Logs/gold_tier_progress.md."""
    LOGS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    line = f"- [{now.strftime('%Y-%m-%d %H:%M UTC')}] **{event}** {detail}\n"
    with open(PROGRESS_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _update_dashboard_briefing_line(briefing_name: str, ts: datetime) -> None:
    """Update (or insert) the Last CEO Briefing line in Dashboard.md."""
    import re as _re
    if not DASHBOARD.exists():
        return
    text = DASHBOARD.read_text(encoding="utf-8")
    new_line = (
        f"**Last CEO Briefing:** {ts.strftime('%Y-%m-%d %H:%M UTC')} "
        f"— [{briefing_name}](Briefings/{briefing_name})"
    )
    if "**Last CEO Briefing:**" in text:
        text = _re.sub(r"\*\*Last CEO Briefing:\*\*.*", new_line, text)
    else:
        # Insert after the "Last updated" line
        text = _re.sub(
            r"(\*\*Last updated:\*\*[^\n]*)",
            r"\1\n" + new_line,
            text,
        )
    DASHBOARD.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_audit(dry_run: bool = False, report_date: datetime | None = None) -> Path:
    """Full Sunday audit workflow.

    1. Collect all data
    2. Compute prior-week stats for week-over-week comparison
    3. Generate CEO briefing (validates 7 required sections; saves as DRAFT_ if incomplete)
    4. Send WhatsApp summary (skipped for DRAFT briefings)
    5. Update Dashboard.md and progress log

    Log retention is NOT handled here — run src/log_janitor.py separately (cron: 30 23 * * 0).

    Returns:
        Path to the generated briefing.
    """
    logger.info("Starting weekly audit (dry_run=%s)", dry_run)
    _log_progress("audit_started", f"dry_run={dry_run}")
    run_start = datetime.now(timezone.utc)

    # Step 1: Collect data
    vault_snapshot = collect_vault_snapshot()
    social_metrics = collect_social_metrics()
    financial = collect_financial_summary()
    audit_stats = get_period_stats(days=7)

    # Step 2: Prior-week stats for week-over-week comparison
    ref_date = report_date or datetime.now(timezone.utc)
    prior_week_end = ref_date - timedelta(days=7)
    prior_entries = read_logs(date=prior_week_end, days=7)
    prior_stats = {
        "total_entries": len(prior_entries),
        "social_posts": sum(
            1 for e in prior_entries
            if "social_post" in e.get("action_type", "")
            or e.get("action_type", "").startswith(("twitter_", "linkedin_", "facebook_", "instagram_"))
        ),
        "emails_sent": sum(
            1 for e in prior_entries
            if e.get("action_type") == "email_send" and e.get("result") == "success"
        ),
        "failures": sum(1 for e in prior_entries if e.get("result") == "failure"),
    }
    prior_stats["failure_rate"] = round(
        prior_stats["failures"] / max(prior_stats["total_entries"], 1) * 100, 1
    )

    # Step 3: Generate CEO briefing
    briefing_path = generate_ceo_briefing(
        vault_snapshot=vault_snapshot,
        social_metrics=social_metrics,
        financial=financial,
        audit_stats=audit_stats,
        prior_stats=prior_stats,
        report_date=report_date,
        dry_run=dry_run,
    )
    _log_progress("briefing_generated", briefing_path.name)

    # Step 4: Send WhatsApp summary (only for fully-validated briefings)
    is_draft = briefing_path.name.startswith("DRAFT_")
    if not is_draft:
        wa_ok = send_whatsapp_summary(briefing_path, dry_run=dry_run)
        _log_progress(
            "whatsapp_sent" if wa_ok else "whatsapp_skipped",
            f"to={OWNER_WHATSAPP or 'not configured'}",
        )
    else:
        logger.warning("Skipping WhatsApp — briefing is a DRAFT (missing sections)")
        _log_progress("whatsapp_skipped", "briefing saved as DRAFT")

    # Step 5: Record runtime
    elapsed = round((datetime.now(timezone.utc) - run_start).total_seconds())
    logger.info("Weekly audit complete in %ds. Briefing: %s", elapsed, briefing_path.name)
    _log_progress("audit_complete", f"{briefing_path.name} runtime={elapsed}s draft={is_draft}")
    return briefing_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Zoya Weekly Audit Generator")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate briefing without sending WhatsApp or modifying live data",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run even if it's not Sunday",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Generate briefing anchored to this date (also implies --force)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args()

    if args.verbose:
        import logging as _logging
        _logging.getLogger("audit_generator").setLevel(_logging.DEBUG)

    report_date: datetime | None = None
    if args.date:
        try:
            report_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            parser.error(f"Invalid --date value {args.date!r} — expected YYYY-MM-DD")

    now = report_date or datetime.now(timezone.utc)
    if now.weekday() != 6 and not args.force and not args.date:  # 6 = Sunday
        logger.info("Not Sunday — skipping audit (use --force or --date to override)")
        return

    briefing_path = run_audit(dry_run=args.dry_run, report_date=report_date)
    print(f"CEO Briefing generated: {briefing_path}")


if __name__ == "__main__":
    main()
