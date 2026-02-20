"""Cross-Domain Orchestrator — Zoya Gold Tier.

Bridges personal and business domains:
- Personal: Gmail, WhatsApp, bank transactions
- Business: social media, invoices, project tasks, client ledger

Bridge rules:
1. WhatsApp message mentions business keywords → auto-create task in Business/Tasks/
2. Bank transaction matches a client name from Clients/ → link to that client's ledger

Entry point:
    uv run python -m src.cross_domain_orchestrator
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.config import DONE, VAULT_PATH
from src.utils import log_action, setup_logger

logger = setup_logger("cross_domain_orchestrator")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BUSINESS_TASKS = VAULT_PATH / "Business" / "Tasks"
CLIENTS = VAULT_PATH / "Clients"
_STATE_FILE = VAULT_PATH / "Logs" / ".cross_domain_processed.json"

# ---------------------------------------------------------------------------
# Business keyword detection
# ---------------------------------------------------------------------------

BUSINESS_KEYWORDS: frozenset[str] = frozenset({
    "invoice",
    "payment",
    "project",
    "client",
    "contract",
    "deadline",
    "proposal",
    "budget",
    "quote",
    "deliverable",
    "milestone",
    "retainer",
    "fee",
    "billing",
})


def _contains_business_keywords(text: str) -> list[str]:
    """Return list of matched business keywords found in text (case-insensitive)."""
    text_lower = text.lower()
    return [kw for kw in BUSINESS_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower)]


# ---------------------------------------------------------------------------
# Processed-item state (prevents duplicate task creation)
# ---------------------------------------------------------------------------

def _load_processed() -> set[str]:
    """Load the set of already-processed item names from the state file."""
    if not _STATE_FILE.exists():
        return set()
    try:
        data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        return set(data.get("processed", []))
    except (json.JSONDecodeError, OSError):
        return set()


def _save_processed(processed: set[str]) -> None:
    """Persist the processed set to disk."""
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(
        json.dumps({"processed": sorted(processed)}, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Frontmatter reader
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


def _read_body(path: Path) -> str:
    """Read the body of a .md file (everything after the first --- block)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    # Strip frontmatter
    stripped = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
    return stripped.strip()


# ---------------------------------------------------------------------------
# Bridge 1: WhatsApp → Business Task
# ---------------------------------------------------------------------------

def _create_business_task(
    source_name: str,
    sender: str,
    keywords: list[str],
    summary: str,
    original_text: str,
) -> Path:
    """Write a business task file in Business/Tasks/.

    Returns the path to the created task file.
    """
    BUSINESS_TASKS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^\w]", "_", source_name)[:40]
    task_path = BUSINESS_TASKS / f"TASK_{ts}_{safe_name}.md"

    kw_str = ", ".join(keywords)
    content = (
        f"---\n"
        f"type: business_task\n"
        f"source: whatsapp\n"
        f"sender: {sender}\n"
        f"created_at: {now.isoformat()}\n"
        f"status: pending\n"
        f"triggered_by: {source_name}\n"
        f"keywords_matched: {kw_str}\n"
        f"---\n\n"
        f"# Business Task (auto-created from WhatsApp)\n\n"
        f"**From:** {sender}  \n"
        f"**Created:** {now.strftime('%Y-%m-%d %H:%M UTC')}  \n"
        f"**Keywords matched:** {kw_str}  \n\n"
        f"## Summary\n\n"
        f"{summary}\n\n"
        f"## Original Message Excerpt\n\n"
        f"{original_text[:800]}\n\n"
        f"## Actions\n\n"
        f"- [ ] Review and action this business item\n"
        f"- [ ] Follow up with {sender}\n\n"
        f"---\n"
        f"*Auto-created by Zoya Cross-Domain Orchestrator — business keywords detected in WhatsApp message.*\n"
    )
    task_path.write_text(content, encoding="utf-8")
    log_action("business_task_created", str(task_path), {
        "source": source_name,
        "sender": sender[:20],
        "keywords": kw_str,
    })
    logger.info("Business task created: %s (keywords: %s)", task_path.name, kw_str)
    return task_path


def scan_whatsapp_for_business_triggers(processed: set[str]) -> list[Path]:
    """Scan Done/ for WhatsApp items containing business keywords.

    For each new item found, creates a task in Business/Tasks/.
    Returns list of task files created.
    """
    if not DONE.exists():
        return []

    tasks_created: list[Path] = []

    for meta_path in DONE.glob("FILE_*.md"):
        if meta_path.name in processed:
            continue

        fm = _read_frontmatter(meta_path)
        if fm.get("source") != "whatsapp":
            continue

        body = _read_body(meta_path)
        full_text = body

        keywords = _contains_business_keywords(full_text)
        if not keywords:
            processed.add(meta_path.name)
            continue

        # Extract summary from ## Summary section
        summary_match = re.search(r"## Summary\s*\n(.*?)(?=\n##|\Z)", body, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else "(no summary)"

        sender = fm.get("sender") or fm.get("from", "unknown")
        original_name = fm.get("original_name", meta_path.name)

        task_path = _create_business_task(
            source_name=original_name,
            sender=sender,
            keywords=keywords,
            summary=summary,
            original_text=body,
        )
        tasks_created.append(task_path)
        processed.add(meta_path.name)

    return tasks_created


# ---------------------------------------------------------------------------
# Bridge 2: Bank transaction → Client ledger
# ---------------------------------------------------------------------------

def _list_clients() -> dict[str, Path]:
    """Return a mapping of lowercased client name → client file path."""
    if not CLIENTS.exists():
        return {}
    clients: dict[str, Path] = {}
    for f in CLIENTS.glob("CLIENT_*.md"):
        fm = _read_frontmatter(f)
        name = fm.get("client_name", "")
        if name:
            clients[name.lower()] = f
        # Also index by filename stem
        stem_name = f.stem[7:].replace("_", " ").lower()  # strip "CLIENT_"
        if stem_name:
            clients[stem_name] = f
    return clients


def _match_client(payee: str, client_map: dict[str, Path]) -> tuple[str, Path] | None:
    """Find the best matching client for a payee name.

    Returns (client_name, client_path) or None if no match.
    """
    payee_lower = payee.lower().strip()
    # Exact match
    if payee_lower in client_map:
        return payee_lower, client_map[payee_lower]
    # Substring match
    for client_name, client_path in client_map.items():
        if client_name in payee_lower or payee_lower in client_name:
            return client_name, client_path
    return None


def _append_to_client_ledger(
    client_path: Path,
    transaction_name: str,
    amount: str,
    date: str,
    description: str,
) -> None:
    """Append a bank transaction entry to a client's ledger section."""
    try:
        text = client_path.read_text(encoding="utf-8")
    except OSError:
        return

    entry = (
        f"| {date} | {transaction_name} | {amount} | {description[:60]} |\n"
    )

    if "## Ledger" in text:
        # Append to existing ledger table
        text = text.rstrip() + "\n" + entry
    else:
        # Add ledger section
        text = text.rstrip() + (
            "\n\n## Ledger\n\n"
            "| Date | Transaction | Amount | Description |\n"
            "|------|-------------|--------|-------------|\n"
            + entry
        )

    # Update last_seen frontmatter
    now_iso = datetime.now(timezone.utc).isoformat()
    text = re.sub(r"(last_transaction:).*", f"\\1 {now_iso[:10]}", text)
    if "last_transaction:" not in text:
        text = re.sub(r"(---\n)", f"last_transaction: {now_iso[:10]}\n\\1", text, count=1)

    client_path.write_text(text, encoding="utf-8")
    logger.info("Appended transaction to client ledger: %s", client_path.name)


def _extract_transaction_details(fm: dict[str, str], body: str) -> dict[str, str]:
    """Extract transaction fields from a bank transaction metadata file."""
    # Try frontmatter first
    amount = fm.get("amount", "")
    payee = fm.get("payee") or fm.get("merchant") or fm.get("description", "")
    date = fm.get("transaction_date") or fm.get("date") or fm.get("queued_at", "")[:10]

    # Fallback: scan body for patterns
    if not amount:
        amt_match = re.search(r"(?:amount|total|paid)[:\s]+\$?([\d,]+(?:\.\d{2})?)", body, re.IGNORECASE)
        if amt_match:
            amount = amt_match.group(1)

    if not payee:
        payee_match = re.search(r"(?:payee|merchant|to)[:\s]+(.+)", body, re.IGNORECASE)
        if payee_match:
            payee = payee_match.group(1).strip()[:60]

    return {"amount": amount, "payee": payee, "date": date}


def scan_bank_transactions(processed: set[str]) -> list[tuple[Path, Path]]:
    """Scan Done/ for bank transaction items and link to client ledgers.

    Returns list of (transaction_meta_path, client_path) tuples for linked transactions.
    """
    if not DONE.exists():
        return []

    client_map = _list_clients()
    if not client_map:
        logger.debug("No clients in Clients/ — skipping bank transaction linking")
        return []

    linked: list[tuple[Path, Path]] = []

    for meta_path in DONE.glob("FILE_*.md"):
        name_key = f"bank_{meta_path.name}"
        if name_key in processed:
            continue

        fm = _read_frontmatter(meta_path)
        doc_type = fm.get("type", "")
        source = fm.get("source", "")

        # Only process bank/transaction items
        if doc_type not in ("bank_transaction", "receipt", "invoice") and source != "bank":
            continue

        body = _read_body(meta_path)
        details = _extract_transaction_details(fm, body)
        payee = details["payee"]

        if not payee:
            processed.add(name_key)
            continue

        match = _match_client(payee, client_map)
        if not match:
            processed.add(name_key)
            continue

        client_name, client_path = match
        _append_to_client_ledger(
            client_path=client_path,
            transaction_name=fm.get("original_name", meta_path.name),
            amount=details["amount"] or "?",
            date=details["date"] or "?",
            description=payee,
        )
        log_action("transaction_linked", str(client_path), {
            "payee": payee[:20],
            "client": client_name[:20],
            "amount": details["amount"],
        })
        linked.append((meta_path, client_path))
        processed.add(name_key)

    return linked


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_cross_domain_cycle() -> dict:
    """Run one cross-domain integration cycle.

    Returns summary dict with counts of actions taken.
    """
    processed = _load_processed()
    initial_count = len(processed)

    # Bridge 1: WhatsApp → Business Tasks
    tasks_created = scan_whatsapp_for_business_triggers(processed)

    # Bridge 2: Bank transactions → Client ledger
    linked_transactions = scan_bank_transactions(processed)

    # Persist updated processed set
    if len(processed) > initial_count:
        _save_processed(processed)

    summary = {
        "business_tasks_created": len(tasks_created),
        "transactions_linked": len(linked_transactions),
    }

    if tasks_created or linked_transactions:
        logger.info(
            "Cross-domain cycle: %d task(s) created, %d transaction(s) linked",
            len(tasks_created),
            len(linked_transactions),
        )
    else:
        logger.debug("Cross-domain cycle: nothing to do")

    return summary


def create_client(name: str, email: str = "", phone: str = "", notes: str = "") -> Path:
    """Create a new client record in Clients/.

    Args:
        name: Client display name (used as identity key).
        email: Client email address.
        phone: Client phone number.
        notes: Any additional notes.

    Returns:
        Path to the created client file.
    """
    CLIENTS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    safe_name = re.sub(r"[^\w]", "_", name)[:50]
    client_path = CLIENTS / f"CLIENT_{safe_name}.md"

    content = (
        f"---\n"
        f"client_name: {name}\n"
        f"email: {email}\n"
        f"phone: {phone}\n"
        f"created_at: {now.isoformat()}\n"
        f"last_transaction:\n"
        f"---\n\n"
        f"# Client: {name}\n\n"
        f"**Email:** {email or '(not set)'}  \n"
        f"**Phone:** {phone or '(not set)'}  \n"
        f"**Since:** {now.strftime('%Y-%m-%d')}  \n\n"
        f"## Notes\n\n"
        f"{notes or '(no notes yet)'}\n\n"
        f"## Ledger\n\n"
        f"| Date | Transaction | Amount | Description |\n"
        f"|------|-------------|--------|-------------|\n"
        f"| (no transactions yet) | | | |\n\n"
        f"---\n"
        f"*Client record maintained by Zoya Cross-Domain Orchestrator.*\n"
    )
    client_path.write_text(content, encoding="utf-8")
    log_action("client_created", str(client_path), {"name": name})
    logger.info("Client created: %s", client_path.name)
    return client_path


def main() -> None:
    """Run one cross-domain integration cycle (for cron / manual invocation)."""
    summary = run_cross_domain_cycle()
    print(
        f"Cross-domain cycle complete: "
        f"{summary['business_tasks_created']} task(s) created, "
        f"{summary['transactions_linked']} transaction(s) linked"
    )


if __name__ == "__main__":
    main()
