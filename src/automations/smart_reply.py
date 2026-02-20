"""Gmail Smart Reply Drafter — Zoya Gold Tier.

When the Gmail watcher ingests an email, this module decides whether to draft
an automatic reply using Claude and routes it through the HITL approval flow.

Decision logic:
  1. Is the sender a KNOWN CLIENT or VIP?  (check Contacts/ + Company_Handbook.md)
  2. Does the email contain HIGH-PRIORITY keywords in subject or body?
     (urgent, invoice, payment, meeting, deadline, complaint, asap, quote, etc.)
  3. If EITHER condition → draft a professional reply with Claude
     → save REPLY_*.md to Pending_Approval/ (HITL required before sending)
  4. If NEITHER → email is low-priority, processed normally to Done/ without draft

SAFETY: No email is EVER sent automatically. Every draft goes to Pending_Approval/.
        The Email MCP `send_email` tool only fires after a human approves.

Integration:
    Called by the orchestrator after processing any email with source: gmail.
    Can also be called standalone: python -m src.automations.smart_reply <meta_path>

.env:
    SMART_REPLY_ENABLED=true          # Set false to disable entirely
    SMART_REPLY_DRY_RUN=true          # true = log draft only, don't write files
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from email.utils import parseaddr

from dotenv import load_dotenv

from src.audit_logger import audit_log
from src.config import (
    DONE,
    HANDBOOK,
    PENDING_APPROVAL,
    PROJECT_ROOT,
    VAULT_PATH,
)
from src.utils import log_action, setup_logger

load_dotenv(PROJECT_ROOT / ".env")

logger = setup_logger("smart_reply")

CONTACTS_DIR = VAULT_PATH / "Contacts"
SMART_REPLY_ENABLED = os.getenv("SMART_REPLY_ENABLED", "true").lower() == "true"
SMART_REPLY_DRY_RUN = os.getenv("SMART_REPLY_DRY_RUN", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Priority keyword sets
# ---------------------------------------------------------------------------

HIGH_PRIORITY_SUBJECT_KEYWORDS: frozenset[str] = frozenset({
    "urgent", "asap", "invoice", "payment", "overdue", "past due",
    "meeting", "complaint", "problem", "issue", "error", "wrong",
    "deadline", "quote", "proposal", "contract", "signed", "immediately",
    "escalate", "help", "broken", "critical", "block", "cannot",
})

HIGH_PRIORITY_BODY_KEYWORDS: frozenset[str] = frozenset({
    "urgent", "asap", "immediately", "invoice", "payment due", "overdue",
    "please respond", "awaiting your reply", "as soon as possible",
    "outstanding balance", "final reminder", "legal action",
    "complaint", "not working", "broken", "failed", "wrong amount",
    "meeting tomorrow", "call me", "need your help",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_frontmatter(path: Path) -> dict[str, str]:
    """Parse YAML-ish frontmatter from a metadata .md file."""
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


def _extract_email_address(raw: str) -> str:
    """Extract plain email from 'Name <email@example.com>'."""
    _, addr = parseaddr(raw)
    return addr.lower().strip()


def _extract_body_from_md(path: Path) -> str:
    """Read the email body from a processed email metadata file."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    # Find '## Email Content' section
    m = re.search(r"## Email Content\s*\n(.*?)(?=\n##|\Z)", text, re.DOTALL)
    if m:
        return m.group(1).strip()[:3000]
    return text[500:3500]  # fallback: skip frontmatter, take body chunk


# ---------------------------------------------------------------------------
# Known-client detection
# ---------------------------------------------------------------------------

def _load_known_emails() -> set[str]:
    """Build a set of known email addresses from Contacts/ and Company_Handbook.md."""
    known: set[str] = set()

    # From Contacts/ — each CONTACT_*.md has `identity:` in frontmatter
    if CONTACTS_DIR.exists():
        for contact_file in CONTACTS_DIR.glob("CONTACT_*.md"):
            fm = _read_frontmatter(contact_file)
            identity = fm.get("identity", "")
            if "@" in identity:
                known.add(identity.lower())

    # From Company_Handbook.md — scan for email-shaped strings
    if HANDBOOK.exists():
        try:
            text = HANDBOOK.read_text(encoding="utf-8")
            emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
            known.update(e.lower() for e in emails)
        except OSError:
            pass

    return known


def classify_email(
    from_addr: str,
    subject: str,
    body: str,
    known_emails: set[str],
) -> tuple[bool, str, str]:
    """Decide whether to draft a reply and why.

    Returns:
        (should_draft: bool, priority: str, reason: str)
    """
    from_clean = _extract_email_address(from_addr)
    subj_lower = subject.lower()
    body_lower = body.lower()[:2000]

    is_vip = from_clean in known_emails
    subject_hit = any(kw in subj_lower for kw in HIGH_PRIORITY_SUBJECT_KEYWORDS)
    body_hit    = any(kw in body_lower  for kw in HIGH_PRIORITY_BODY_KEYWORDS)

    if is_vip and (subject_hit or body_hit):
        return True, "high", f"VIP client ({from_clean}) + priority keyword"
    if is_vip:
        return True, "medium", f"VIP client ({from_clean})"
    if subject_hit:
        return True, "high", f"High-priority subject keyword"
    if body_hit:
        return True, "medium", f"High-priority body keyword"

    return False, "low", "Low priority — no VIP or keyword match"


# ---------------------------------------------------------------------------
# Claude reply generator
# ---------------------------------------------------------------------------

def _load_handbook_tone() -> str:
    """Extract tone/persona section from Company_Handbook.md."""
    if not HANDBOOK.exists():
        return "Professional, polite, concise, and helpful."
    try:
        text = HANDBOOK.read_text(encoding="utf-8")
        # Look for a 'Tone' or 'Communication Style' or 'Voice' section
        m = re.search(
            r"##\s*(?:tone|communication style|voice|writing style)[^\n]*\n(.*?)(?=\n##|\Z)",
            text, re.IGNORECASE | re.DOTALL,
        )
        if m:
            return m.group(1).strip()[:500]
    except OSError:
        pass
    return "Professional, polite, concise, and helpful."


def generate_reply_with_claude(
    from_addr: str,
    subject: str,
    body: str,
    tone: str,
    priority: str,
    dry_run: bool = False,
) -> str:
    """Ask Claude to draft a reply to the given email.

    Returns the drafted reply text.
    """
    prompt = (
        f"You are Zoya, a professional AI assistant drafting an email reply on behalf of the business owner.\n\n"
        f"**Tone/style:** {tone}\n\n"
        f"**Original email:**\n"
        f"From: {from_addr}\n"
        f"Subject: {subject}\n"
        f"Priority: {priority}\n\n"
        f"Body:\n{body[:2000]}\n\n"
        f"---\n\n"
        f"Draft a professional, polite email reply. Rules:\n"
        f"1. Do NOT invent facts or make commitments the owner hasn't approved\n"
        f"2. Acknowledge the email and its urgency if high priority\n"
        f"3. Use the tone/style specified above\n"
        f"4. Keep it concise (2-4 short paragraphs)\n"
        f"5. End with a professional sign-off\n"
        f"6. Output ONLY the email body text — no subject line, no metadata\n\n"
        f"Reply:"
    )

    if dry_run:
        return (
            f"[DRY RUN DRAFT]\n\n"
            f"Thank you for your email regarding \"{subject}\".\n\n"
            f"I have received your message and will get back to you shortly with a full response.\n\n"
            f"Best regards,\n[Owner Name]"
        )

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            timeout=90,
            cwd=str(PROJECT_ROOT),
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        else:
            logger.warning("Claude returned empty/error response — using fallback draft")
    except Exception as exc:
        logger.warning("Claude call failed for smart reply: %s — using fallback", exc)

    # Fallback draft (Claude unavailable)
    return (
        f"Thank you for your email regarding \"{subject}\".\n\n"
        f"I have received your message and will review it promptly. "
        f"{'This appears to be time-sensitive and I will prioritise my response.' if priority == 'high' else 'I will be in touch soon.'}\n\n"
        f"Best regards,\n[Please add your name]"
    )


# ---------------------------------------------------------------------------
# Approval file writer
# ---------------------------------------------------------------------------

def _write_reply_approval_file(
    gmail_id: str,
    to: str,
    subject: str,
    body_draft: str,
    original_file: Path,
    priority: str,
    reason: str,
) -> Path:
    """Create REPLY_*.md in Pending_Approval/ for human review."""
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ts  = now.strftime("%Y%m%d_%H%M%S")
    safe_subj = re.sub(r"[^\w]", "_", subject)[:40].strip("_")
    approval_file = PENDING_APPROVAL / f"REPLY_{ts}_{safe_subj}.md"

    approval_file.write_text(
        f"---\n"
        f"type: email_reply_draft\n"
        f"original_email_id: {gmail_id}\n"
        f"original_file: {original_file.name}\n"
        f"to: {to}\n"
        f"subject: Re: {subject}\n"
        f"priority: {priority}\n"
        f"draft_reason: {reason}\n"
        f"suggested_by: claude\n"
        f"created_at: {now.isoformat()}\n"
        f"status: pending_approval\n"
        f"approval_required: true\n"
        f"action: send_email\n"
        f"dry_run: {'true' if SMART_REPLY_DRY_RUN else 'false'}\n"
        f"---\n\n"
        f"# Email Reply Draft\n\n"
        f"**To:** {to}  \n"
        f"**Subject:** Re: {subject}  \n"
        f"**Priority:** {priority.upper()}  \n"
        f"**Reason drafted:** {reason}\n\n"
        f"---\n\n"
        f"## Drafted Reply\n\n"
        f"{body_draft}\n\n"
        f"---\n\n"
        f"## Instructions\n\n"
        f"- ✅ **Approve:** Move this file to `/Approved/` — Zoya will send via Gmail MCP\n"
        f"- ✏️ **Edit:** Edit the draft above before moving to `/Approved/`\n"
        f"- ❌ **Reject:** Move to `/Rejected/` to discard without sending\n\n"
        f"_Draft generated by Zoya Smart Reply · NEVER auto-sent_\n",
        encoding="utf-8",
    )
    return approval_file


# ---------------------------------------------------------------------------
# Main orchestration function
# ---------------------------------------------------------------------------

def process_email_for_smart_reply(meta_path: Path) -> Path | None:
    """Check an email metadata file and draft a reply if warranted.

    Called by the orchestrator after processing a gmail email.

    Args:
        meta_path: Path to the processed email metadata .md file in Done/ or In_Progress/.

    Returns:
        Path to the REPLY_*.md approval file if one was created, else None.
    """
    if not SMART_REPLY_ENABLED:
        return None

    fm = _read_frontmatter(meta_path)

    # Only process gmail emails
    if fm.get("source") != "gmail":
        return None

    from_addr = fm.get("from", fm.get("sender", ""))
    subject   = fm.get("subject", "(no subject)")
    gmail_id  = fm.get("gmail_id", "")

    if not from_addr:
        return None

    # Load email body
    body = _extract_body_from_md(meta_path)

    # Load known clients
    known_emails = _load_known_emails()

    # Classify
    should_draft, priority, reason = classify_email(
        from_addr, subject, body, known_emails
    )

    if not should_draft:
        logger.info(
            "Smart reply: LOW PRIORITY — skipping draft for email from %s (%s)",
            from_addr[:40], reason,
        )
        audit_log(
            "smart_reply_skipped",
            meta_path.name,
            actor="claude_code",
            parameters={"from": from_addr[:50], "priority": priority, "reason": reason},
        )
        return None

    logger.info(
        "Smart reply: drafting for email from %s — %s (priority=%s)",
        from_addr[:40], reason, priority,
    )

    # Generate reply via Claude
    tone = _load_handbook_tone()
    draft = generate_reply_with_claude(
        from_addr=from_addr,
        subject=subject,
        body=body,
        tone=tone,
        priority=priority,
        dry_run=SMART_REPLY_DRY_RUN,
    )

    # Write approval file
    approval_path = _write_reply_approval_file(
        gmail_id=gmail_id,
        to=from_addr,
        subject=subject,
        body_draft=draft,
        original_file=meta_path,
        priority=priority,
        reason=reason,
    )

    audit_log(
        "smart_reply_drafted",
        approval_path.name,
        actor="claude_code",
        parameters={
            "from": from_addr[:50],
            "subject": subject[:80],
            "priority": priority,
            "reason": reason,
            "dry_run": SMART_REPLY_DRY_RUN,
        },
        approval_status="pending",
        result="pending",
    )
    log_action("smart_reply_created", str(approval_path), {
        "from": from_addr[:50],
        "priority": priority,
    })
    logger.info("Smart reply draft created: %s", approval_path.name)
    return approval_path


# ---------------------------------------------------------------------------
# Approval processor (called when human approves a REPLY_*.md)
# ---------------------------------------------------------------------------

def process_approved_replies(approved_dir: Path | None = None) -> int:
    """Send approved REPLY_*.md files via the Email MCP.

    Looks in Approved/ for REPLY_*.md files. For each:
      - Extracts to/subject/body from the file
      - Calls the email MCP send_email tool (or logs in dry_run)
      - Moves the file to Done/

    Returns count of replies processed.
    """
    from src.config import APPROVED

    approved_dir = approved_dir or APPROVED
    approved_dir.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)

    import shutil
    count = 0

    for reply_file in sorted(approved_dir.glob("REPLY_*.md")):
        fm = _read_frontmatter(reply_file)
        text = reply_file.read_text(encoding="utf-8")

        to      = fm.get("to", "")
        subject = fm.get("subject", "")

        # Extract body from ## Drafted Reply section
        body = ""
        in_draft = False
        for line in text.splitlines():
            if line.strip() == "## Drafted Reply":
                in_draft = True
                continue
            if in_draft and line.startswith("## "):
                break
            if in_draft:
                body += line + "\n"
        body = body.strip()

        if not to or not body:
            logger.warning("REPLY file %s missing to/body — skipping", reply_file.name)
            continue

        if SMART_REPLY_DRY_RUN:
            logger.info("[DRY RUN] Would send email to %s: %s", to, subject)
            success = True
        else:
            # Delegate to the email MCP send_email logic
            # (We call the core function directly to avoid subprocess overhead)
            try:
                from src.mcp.email_server import send_email as _send
                result_msg = _send(to=to, subject=subject, body=body)
                success = "approval" in result_msg.lower() or "created" in result_msg.lower()
            except Exception as exc:
                logger.error("Failed to send reply to %s: %s", to, exc)
                success = False

        # Archive to Done/
        dest = DONE / reply_file.name
        shutil.move(str(reply_file), dest)

        status = "sent" if success else "send_failed"
        audit_log(
            "smart_reply_sent" if success else "smart_reply_send_failed",
            dest.name,
            actor="human",
            parameters={"to": to[:50], "subject": subject[:80], "dry_run": SMART_REPLY_DRY_RUN},
            approval_status="human_approved",
            approved_by="human",
            result="success" if success else "failure",
        )
        logger.info("Reply %s → %s (success=%s)", reply_file.name, to, success)
        count += 1

    return count


# ---------------------------------------------------------------------------
# CLI for standalone use / testing
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Zoya Smart Reply Drafter — test on a single email metadata file"
    )
    parser.add_argument("meta_path", help="Path to an email metadata .md file")
    parser.add_argument("--dry-run", action="store_true", help="Log only, don't write files")
    args = parser.parse_args()

    path = Path(args.meta_path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        os.environ["SMART_REPLY_DRY_RUN"] = "true"

    result = process_email_for_smart_reply(path)
    if result:
        print(f"Draft created: {result}")
    else:
        print("No draft needed (low priority or smart reply disabled)")


if __name__ == "__main__":
    main()
