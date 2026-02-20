"""Source Normalizer — unified metadata format across all input sources.

All sources (file_drop, gmail, whatsapp) produce metadata in slightly
different formats. This module normalizes them into a standard structure
for the orchestrator.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Priority ordering: WhatsApp urgent > email > file
SOURCE_PRIORITY = {
    "whatsapp": 3,  # Highest — real-time, expects quick response
    "gmail": 2,     # Medium — emails can wait a bit
    "file_drop": 1, # Lowest — dropped files are least urgent
}


def normalize_metadata(source_type: str, raw: dict[str, str]) -> dict[str, str]:
    """Normalize metadata from any source into a standard format.

    Args:
        source_type: One of "file_drop", "gmail", "whatsapp".
        raw: Raw frontmatter dict from the metadata file.

    Returns:
        Normalized metadata dict with consistent keys.
    """
    normalized = {
        "source": source_type,
        "original_name": raw.get("original_name", raw.get("subject", "unknown")),
        "status": raw.get("status", "pending"),
        "priority": raw.get("priority", "low"),
        "type": raw.get("type", "other"),
        "received_at": raw.get("queued_at", raw.get("received", datetime.now(timezone.utc).isoformat())),
        "retry_count": raw.get("retry_count", "0"),
        "content_hash": raw.get("content_hash", ""),
    }

    # Source-specific fields
    if source_type == "gmail":
        normalized["sender"] = raw.get("from", "")
        normalized["subject"] = raw.get("subject", "")
        normalized["gmail_id"] = raw.get("gmail_id", "")
    elif source_type == "whatsapp":
        normalized["sender"] = raw.get("from", "")
        normalized["message_type"] = raw.get("message_type", "text")

    return normalized


def get_source_priority(source: str) -> int:
    """Return the priority weight for a source type.

    Higher value = higher processing priority.
    """
    return SOURCE_PRIORITY.get(source, 0)


def sort_by_priority(items: list[dict[str, str]]) -> list[dict[str, str]]:
    """Sort metadata items by source priority (highest first), then by received time."""
    return sorted(
        items,
        key=lambda x: (
            -get_source_priority(x.get("source", "file_drop")),
            x.get("received_at", ""),
        ),
    )
