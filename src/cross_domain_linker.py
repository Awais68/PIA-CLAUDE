"""Cross-Domain Contact Linker — Zoya Gold Tier G3.

Links related items across WhatsApp, Gmail, and file channels.
Creates and maintains CONTACT_*.md files in AI_Employee_Vault/Contacts/.

A contact record aggregates all interactions from a person/entity across
all channels so Zoya can see the full picture of a relationship.

Contact identity resolution:
- Email address (Gmail)
- Phone number (WhatsApp)
- Name (extracted from documents)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from src.config import DONE, NEEDS_ACTION, PENDING_APPROVAL, VAULT_PATH
from src.utils import log_action, setup_logger

logger = setup_logger("cross_domain_linker")

# Contacts folder
CONTACTS = VAULT_PATH / "Contacts"


# ---------------------------------------------------------------------------
# Identity extraction helpers
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


def normalize_phone(phone: str) -> str:
    """Normalize a phone number to digits-only E.164-ish format."""
    digits = re.sub(r"[^\d+]", "", phone)
    return digits


def extract_email(raw: str) -> str | None:
    """Extract a clean email address from a raw string like 'Name <email@example.com>'."""
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw)
    return match.group(0).lower() if match else None


def make_contact_key(identity: str) -> str:
    """Create a filesystem-safe contact key from an email or phone."""
    # Email: alice@example.com → alice_at_example_com
    key = identity.lower()
    key = key.replace("@", "_at_").replace(".", "_").replace("+", "")
    key = re.sub(r"[^\w]", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    return key[:60]  # cap length


def get_contact_identity(fm: dict[str, str]) -> tuple[str, str] | None:
    """Extract contact identity from item frontmatter.

    Returns (identity_string, channel) or None if not identifiable.
    """
    source = fm.get("source", "file_drop")

    if source == "gmail":
        sender = fm.get("sender") or fm.get("from", "")
        email = extract_email(sender)
        if email:
            return email, "gmail"

    elif source == "whatsapp":
        sender = fm.get("sender") or fm.get("from", "")
        if sender:
            return normalize_phone(sender), "whatsapp"

    elif source == "file_drop":
        # Try to get sender from document content
        original_name = fm.get("original_name", "")
        # Can't reliably extract identity from file drops — skip
        return None

    return None


# ---------------------------------------------------------------------------
# Contact record management
# ---------------------------------------------------------------------------

def get_contact_path(identity: str) -> Path:
    """Return the path for a contact's .md file."""
    key = make_contact_key(identity)
    return CONTACTS / f"CONTACT_{key}.md"


def load_contact(identity: str) -> dict:
    """Load an existing contact record, or return a blank template."""
    path = get_contact_path(identity)
    if not path.exists():
        return {
            "identity": identity,
            "channels": [],
            "interactions": [],
            "created_at": None,
        }

    fm = _read_frontmatter(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        text = ""

    # Parse interaction lines from the Interactions section
    interactions = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("## Interactions"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            in_section = False
        if in_section and line.startswith("- "):
            interactions.append(line[2:].strip())

    channels = [c.strip() for c in fm.get("channels", "").split(",") if c.strip()]

    return {
        "identity": identity,
        "channels": channels,
        "interactions": interactions,
        "created_at": fm.get("created_at"),
        "display_name": fm.get("display_name", identity),
        "last_seen": fm.get("last_seen", ""),
    }


def save_contact(identity: str, contact: dict) -> Path:
    """Write a contact record to disk.

    Creates or updates CONTACT_*.md in Contacts/.
    """
    CONTACTS.mkdir(parents=True, exist_ok=True)
    path = get_contact_path(identity)
    now = datetime.now(timezone.utc)

    created_at = contact.get("created_at") or now.isoformat()
    display_name = contact.get("display_name", identity)
    channels = sorted(set(contact.get("channels", [])))
    interactions = contact.get("interactions", [])[-50:]  # keep last 50
    last_seen = contact.get("last_seen") or now.isoformat()

    interaction_lines = "\n".join(f"- {i}" for i in interactions) if interactions else "- (no interactions yet)"

    content = (
        f"---\n"
        f"identity: {identity}\n"
        f"display_name: {display_name}\n"
        f"channels: {', '.join(channels)}\n"
        f"created_at: {created_at}\n"
        f"last_seen: {last_seen}\n"
        f"interaction_count: {len(interactions)}\n"
        f"---\n\n"
        f"# Contact: {display_name}\n\n"
        f"**Identity:** `{identity}`  \n"
        f"**Channels:** {', '.join(channels) or 'unknown'}  \n"
        f"**First seen:** {created_at[:10]}  \n"
        f"**Last seen:** {last_seen[:10]}  \n"
        f"**Interactions:** {len(interactions)}\n\n"
        f"## Interactions\n\n"
        f"{interaction_lines}\n\n"
        f"---\n"
        f"*Contact record maintained by Zoya Cross-Domain Linker*\n"
    )

    path.write_text(content, encoding="utf-8")
    return path


def record_interaction(identity: str, channel: str, item_name: str, doc_type: str, timestamp: str) -> Path:
    """Add an interaction to a contact's record.

    Args:
        identity: Email or phone number.
        channel: Source channel (gmail/whatsapp/file_drop).
        item_name: Name of the document/message.
        doc_type: Document type (invoice/email/text/etc).
        timestamp: ISO timestamp of the interaction.

    Returns:
        Path to the updated contact file.
    """
    contact = load_contact(identity)

    # Add channel if not seen before
    if channel not in contact["channels"]:
        contact["channels"].append(channel)

    # Add interaction entry
    ts_short = timestamp[:16] if len(timestamp) >= 16 else timestamp
    interaction = f"[{ts_short}] [{channel}] {doc_type}: {item_name}"
    contact["interactions"].append(interaction)
    contact["last_seen"] = timestamp

    if not contact.get("created_at"):
        contact["created_at"] = timestamp

    path = save_contact(identity, contact)
    logger.info("Recorded interaction for %s via %s", identity[:20], channel)
    return path


# ---------------------------------------------------------------------------
# Link builder — processes vault items to build contact graph
# ---------------------------------------------------------------------------

def process_item_for_contacts(meta_path: Path) -> Path | None:
    """Process a single metadata file and update the contact record if applicable.

    Returns the contact file path if a contact was found/created, else None.
    """
    fm = _read_frontmatter(meta_path)
    identity_result = get_contact_identity(fm)
    if not identity_result:
        return None

    identity, channel = identity_result
    item_name = fm.get("original_name", meta_path.name)
    doc_type = fm.get("type", "other")
    timestamp = fm.get("processed_at") or fm.get("queued_at") or datetime.now(timezone.utc).isoformat()

    path = record_interaction(identity, channel, item_name, doc_type, timestamp)
    log_action("contact_linked", str(path), {
        "identity": identity[:20],
        "channel": channel,
        "item": item_name,
    })
    return path


def build_contact_graph(scan_done: bool = True, scan_pending: bool = True) -> dict:
    """Scan vault folders and build/update all contact records.

    Args:
        scan_done: Include Done/ folder.
        scan_pending: Include Needs_Action/ and Pending_Approval/.

    Returns:
        Dict with summary stats.
    """
    folders: list[Path] = []
    if scan_done and DONE.exists():
        folders.append(DONE)
    if scan_pending:
        if NEEDS_ACTION.exists():
            folders.append(NEEDS_ACTION)
        if PENDING_APPROVAL.exists():
            folders.append(PENDING_APPROVAL)

    contacts_updated: set[str] = set()
    items_processed = 0

    for folder in folders:
        for f in folder.glob("*.md"):
            fm = _read_frontmatter(f)
            result = get_contact_identity(fm)
            if result:
                identity, channel = result
                process_item_for_contacts(f)
                contacts_updated.add(identity)
                items_processed += 1

    logger.info(
        "Contact graph built: %d items → %d contacts",
        items_processed,
        len(contacts_updated),
    )
    return {
        "contacts_updated": len(contacts_updated),
        "items_processed": items_processed,
    }


def find_related_items(identity: str) -> list[Path]:
    """Find all vault items associated with a given identity.

    Returns list of metadata file paths sorted newest first.
    """
    related = []
    folders = [DONE, NEEDS_ACTION, PENDING_APPROVAL]

    for folder in folders:
        if not folder.exists():
            continue
        for f in folder.glob("*.md"):
            fm = _read_frontmatter(f)
            result = get_contact_identity(fm)
            if result and result[0] == identity:
                related.append(f)

    return sorted(related, key=lambda p: p.stat().st_mtime, reverse=True)


def list_contacts() -> list[Path]:
    """Return all contact files sorted by last_seen (newest first)."""
    if not CONTACTS.exists():
        return []
    return sorted(
        CONTACTS.glob("CONTACT_*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
