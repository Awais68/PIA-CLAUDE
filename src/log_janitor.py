"""Log Janitor — Gold Tier Task 8B.

Deletes audit log files older than LOG_RETENTION_DAYS from AI_Employee_Vault/Logs/.
Runs as a separate cron job, 30 minutes AFTER the Sunday CEO Briefing generation.

Why separate from audit_generator?
  The CEO Briefing reads logs to compile stats. If log purge ran first (or during
  briefing generation) the briefing could lose data. Running 30 min later ensures
  the briefing is already written and WhatsApp'd before any logs are removed.

Cron schedule (Sunday 23:30 local — 30 min after audit_generator):
    30 23 * * 0  cd /path/to/project && uv run python -m src.log_janitor

Files this module will DELETE (matching YYYY-MM-DD.json pattern):
  - AI_Employee_Vault/Logs/2025-10-01.json  (if older than retention days)
  - AI_Employee_Vault/Logs/2025-11-15.json

Files this module will NEVER delete (no YYYY-MM-DD pattern, or explicitly skipped):
  - gold_tier_progress.md     (permanent progress log)
  - .cross_domain_processed.json  (deduplication state)
  - .seen_hashes.json         (deduplication state)
  - .ralph_state.json         (Ralph Wiggum state)
  - Any file whose stem does not match YYYY-MM-DD exactly

.env variables:
  LOG_RETENTION_DAYS=90   # default 90 — delete logs older than this
  LOG_DRY_RUN=false       # set true to preview without deleting

Entry point:
    uv run python -m src.log_janitor [--dry-run] [--retention-days N] [--verbose]
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import LOGS, VAULT_PATH
from src.utils import setup_logger

logger = setup_logger("log_janitor")

# Files (by name) that must never be deleted regardless of age
_SKIP_FILES: frozenset[str] = frozenset({
    "gold_tier_progress.md",
    ".cross_domain_processed.json",
    ".seen_hashes.json",
    ".ralph_state.json",
    ".gitkeep",
})

_PROGRESS_LOG = LOGS / "gold_tier_progress.md"
_DATE_FMT = "%Y-%m-%d"


def _is_date_log(path: Path) -> bool:
    """Return True only if the filename stem is exactly YYYY-MM-DD."""
    try:
        datetime.strptime(path.stem, _DATE_FMT)
        return True
    except ValueError:
        return False


def purge_logs(
    retention_days: int = 90,
    dry_run: bool = False,
) -> dict[str, int]:
    """Delete date-pattern log files older than *retention_days*.

    Args:
        retention_days: Minimum age in days before a log file is eligible.
        dry_run:        If True, log what would be deleted but don't delete.

    Returns:
        Dict with keys ``deleted``, ``skipped``, ``eligible``.
    """
    if not LOGS.exists():
        logger.info("Logs folder does not exist yet — nothing to purge")
        return {"deleted": 0, "skipped": 0, "eligible": 0}

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    stats = {"deleted": 0, "skipped": 0, "eligible": 0}

    for log_file in sorted(LOGS.iterdir()):
        if not log_file.is_file():
            continue

        # Never touch explicitly protected files
        if log_file.name in _SKIP_FILES:
            logger.debug("Protected — skipping: %s", log_file.name)
            stats["skipped"] += 1
            continue

        # Only process files whose name is a plain date (YYYY-MM-DD.*)
        if not _is_date_log(log_file):
            logger.debug("Non-date filename — skipping: %s", log_file.name)
            stats["skipped"] += 1
            continue

        # Parse the date from the stem
        file_date = datetime.strptime(log_file.stem, _DATE_FMT).replace(tzinfo=timezone.utc)
        if file_date >= cutoff:
            logger.debug("Within retention window — keeping: %s", log_file.name)
            stats["skipped"] += 1
            continue

        stats["eligible"] += 1
        age_days = (datetime.now(timezone.utc) - file_date).days

        if dry_run:
            logger.info("[DRY RUN] Would delete: %s (%d days old)", log_file.name, age_days)
        else:
            try:
                log_file.unlink()
                logger.info("Deleted: %s (%d days old)", log_file.name, age_days)
                stats["deleted"] += 1
            except OSError as exc:
                logger.error("Failed to delete %s: %s", log_file.name, exc)

    return stats


def _append_progress(stats: dict[str, int], retention_days: int, dry_run: bool) -> None:
    """Append a summary line to gold_tier_progress.md."""
    LOGS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    action = "DRY_RUN" if dry_run else "purge"
    line = (
        f"- [{now.strftime('%Y-%m-%d %H:%M UTC')}] **log_janitor_{action}** "
        f"deleted={stats['deleted']} eligible={stats['eligible']} "
        f"skipped={stats['skipped']} retention={retention_days}d\n"
    )
    with open(_PROGRESS_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def main() -> None:
    # Read defaults from env
    env_retention = int(os.getenv("LOG_RETENTION_DAYS", "90"))
    env_dry_run = os.getenv("LOG_DRY_RUN", "false").lower() == "true"

    parser = argparse.ArgumentParser(
        description="Zoya Log Janitor — purge old audit logs from Vault/Logs/"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=env_dry_run,
        help="Preview deletions without actually removing files (default: LOG_DRY_RUN env)",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=env_retention,
        metavar="N",
        help=f"Delete logs older than N days (default: {env_retention} from LOG_RETENTION_DAYS)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    args = parser.parse_args()

    if args.verbose:
        import logging as _logging
        _logging.getLogger("log_janitor").setLevel(_logging.DEBUG)

    if args.dry_run:
        logger.info(
            "[DRY RUN] Log janitor — retention=%d days, logs folder: %s",
            args.retention_days,
            LOGS,
        )
    else:
        logger.info(
            "Log janitor starting — retention=%d days, logs folder: %s",
            args.retention_days,
            LOGS,
        )

    stats = purge_logs(retention_days=args.retention_days, dry_run=args.dry_run)

    _append_progress(stats, args.retention_days, args.dry_run)

    action_word = "Would delete" if args.dry_run else "Deleted"
    print(
        f"Log janitor complete — {action_word} {stats['eligible']} eligible file(s) "
        f"({stats['deleted']} deleted, {stats['skipped']} skipped)"
    )


if __name__ == "__main__":
    main()
