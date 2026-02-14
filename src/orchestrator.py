"""
Orchestrator for Zoya.

Polls Needs_Action/ for pending metadata files and invokes Claude Code
to process them ONE AT A TIME (claim-by-move pattern).

Flow:
  1. Acquire process lock (only one orchestrator at a time).
  2. Poll Needs_Action/ for .md files with status: pending.
  3. Claim a file by moving it + its companion to In_Progress/.
  4. Invoke Claude Code with the inbox-processor skill prompt.
  5. On success: move to Done/.  On failure: increment retry_count
     or quarantine after MAX_RETRIES.
  6. Trigger dashboard-updater skill.
  7. Loop.
"""

import atexit
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.config import (
    DASHBOARD,
    DONE,
    IN_PROGRESS,
    MAX_BATCH_SIZE,
    MAX_RETRIES,
    NEEDS_ACTION,
    ORCHESTRATOR_LOCK,
    ORCHESTRATOR_POLL_INTERVAL,
    PROJECT_ROOT,
    QUARANTINE,
    VAULT_PATH,
)
from src.utils import acquire_lock, log_action, release_lock, setup_logger

logger = setup_logger("orchestrator")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_frontmatter(path: Path) -> dict[str, str]:
    """Parse YAML-ish frontmatter from a metadata .md file."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def _update_frontmatter(path: Path, updates: dict[str, str]) -> None:
    """Update specific keys in the frontmatter of a metadata file."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return

    fm_lines = match.group(1).splitlines()
    new_lines: list[str] = []
    updated_keys: set[str] = set()
    for line in fm_lines:
        if ":" in line:
            key = line.partition(":")[0].strip()
            if key in updates:
                new_lines.append(f"{key}: {updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Add any keys that weren't already present
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}: {val}")

    new_fm = "---\n" + "\n".join(new_lines) + "\n---"
    rest = text[match.end():]
    path.write_text(new_fm + rest, encoding="utf-8")


def _find_companion(meta_path: Path, source_dir: Path) -> Path | None:
    """Find the original file that accompanies a metadata .md file.

    Metadata file: FILE_20260214_120000_report.md
    Companion:     FILE_20260214_120000_report.pdf (or .docx, etc.)
    """
    stem = meta_path.stem  # e.g. FILE_20260214_120000_report
    for f in source_dir.iterdir():
        if f.stem == stem and f.suffix != ".md":
            return f
    return None


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def claim_file(meta_path: Path) -> tuple[Path, Path | None]:
    """Move metadata + companion from Needs_Action to In_Progress (claim)."""
    new_meta = IN_PROGRESS / meta_path.name
    shutil.move(str(meta_path), new_meta)

    companion = _find_companion(meta_path, NEEDS_ACTION)
    new_companion = None
    if companion and companion.exists():
        new_companion = IN_PROGRESS / companion.name
        shutil.move(str(companion), new_companion)

    _update_frontmatter(new_meta, {"status": "in_progress"})
    log_action("file_claimed", str(new_meta))
    return new_meta, new_companion


def process_with_claude(meta_path: Path, companion: Path | None) -> bool:
    """Invoke Claude Code to process a single file.

    Returns True on success, False on failure.
    """
    fm = _read_frontmatter(meta_path)
    original_name = fm.get("original_name", meta_path.name)

    # Build the file path Claude should read
    file_to_read = str(companion) if companion else str(meta_path)

    prompt = (
        f"You are Zoya, a Personal AI Employee. "
        f"Process this document using the inbox-processor skill.\n\n"
        f"**File to process:** `{file_to_read}`\n"
        f"**Metadata file:** `{meta_path}`\n"
        f"**Original filename:** {original_name}\n\n"
        f"Instructions:\n"
        f"1. Read the file at the path above.\n"
        f"2. Generate a 2-3 sentence summary.\n"
        f"3. Extract all action items (deadlines, tasks, follow-ups).\n"
        f"4. Categorize: invoice, contract, proposal, receipt, note, or other.\n"
        f"5. Assign priority: high (invoices, contracts), medium (proposals), low (other).\n"
        f"6. Write the processed results back to the metadata file at `{meta_path}` "
        f"using the format defined in the inbox-processor skill.\n"
        f"7. Update the frontmatter status to 'done'.\n"
        f"8. Do NOT move files — the orchestrator handles that.\n"
    )

    logger.info("Invoking Claude Code for: %s", original_name)

    try:
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
        )
        if result.returncode == 0:
            logger.info("Claude processed successfully: %s", original_name)
            return True
        else:
            logger.error(
                "Claude failed (exit %d) for %s: %s",
                result.returncode,
                original_name,
                result.stderr[:500],
            )
            return False
    except subprocess.TimeoutExpired:
        logger.error("Claude timed out processing: %s", original_name)
        return False
    except FileNotFoundError:
        logger.error(
            "Claude Code CLI not found. Install with: npm install -g @anthropic/claude-code"
        )
        return False


def move_to_done(meta_path: Path, companion: Path | None) -> None:
    """Move processed files from In_Progress to Done."""
    dest_meta = DONE / meta_path.name
    shutil.move(str(meta_path), dest_meta)
    if companion and companion.exists():
        shutil.move(str(companion), DONE / companion.name)
    _update_frontmatter(dest_meta, {
        "status": "done",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    })
    log_action("file_done", str(dest_meta))
    logger.info("Moved to Done: %s", dest_meta.name)


def handle_failure(meta_path: Path, companion: Path | None) -> None:
    """Increment retry count or quarantine after max retries."""
    fm = _read_frontmatter(meta_path)
    retry_count = int(fm.get("retry_count", "0")) + 1

    if retry_count >= MAX_RETRIES:
        logger.warning(
            "Max retries (%d) reached for %s — quarantining",
            MAX_RETRIES,
            meta_path.name,
        )
        shutil.move(str(meta_path), QUARANTINE / meta_path.name)
        if companion and companion.exists():
            shutil.move(str(companion), QUARANTINE / companion.name)
        _update_frontmatter(
            QUARANTINE / meta_path.name,
            {"status": "quarantined", "reason": f"Failed after {MAX_RETRIES} attempts"},
        )
        log_action("file_quarantined", str(meta_path), {"retries": retry_count})
    else:
        # Move back to Needs_Action for retry
        dest = NEEDS_ACTION / meta_path.name
        shutil.move(str(meta_path), dest)
        if companion and companion.exists():
            shutil.move(str(companion), NEEDS_ACTION / companion.name)
        _update_frontmatter(dest, {
            "status": "pending",
            "retry_count": str(retry_count),
        })
        log_action("file_retry", str(dest), {"retry_count": retry_count})
        logger.info("Retry %d/%d for %s", retry_count, MAX_RETRIES, meta_path.name)


def update_dashboard() -> None:
    """Invoke Claude to refresh Dashboard.md."""
    prompt = (
        f"You are Zoya. Update the dashboard at `{DASHBOARD}`.\n\n"
        f"1. Count files in each vault folder:\n"
        f"   - Inbox: `{VAULT_PATH / 'Inbox'}`\n"
        f"   - Needs_Action: `{VAULT_PATH / 'Needs_Action'}`\n"
        f"   - In_Progress: `{VAULT_PATH / 'In_Progress'}`\n"
        f"   - Done: `{VAULT_PATH / 'Done'}`\n"
        f"   - Quarantine: `{VAULT_PATH / 'Quarantine'}`\n"
        f"2. List the 10 most recent items in Done/ (read their summaries).\n"
        f"3. Note any items in Quarantine as alerts.\n"
        f"4. Write the updated dashboard to `{DASHBOARD}` using the "
        f"dashboard-updater skill format.\n"
        f"5. Set last_updated in the frontmatter to now.\n"
    )
    try:
        subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT),
        )
        logger.info("Dashboard updated.")
    except Exception:
        logger.exception("Dashboard update failed (non-critical)")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_cycle() -> int:
    """Process one batch of pending files. Returns number processed."""
    pending = sorted(
        NEEDS_ACTION.glob("FILE_*.md"),
        key=lambda p: p.stat().st_mtime,
    )

    # Filter to only status: pending
    actionable = []
    for p in pending:
        fm = _read_frontmatter(p)
        if fm.get("status") == "pending":
            actionable.append(p)
        if len(actionable) >= MAX_BATCH_SIZE:
            break

    if not actionable:
        return 0

    logger.info("Processing %d file(s) this cycle", len(actionable))
    processed = 0

    for meta_path in actionable:
        # Claim
        in_prog_meta, in_prog_companion = claim_file(meta_path)

        # Process
        success = process_with_claude(in_prog_meta, in_prog_companion)

        if success:
            move_to_done(in_prog_meta, in_prog_companion)
            processed += 1
        else:
            handle_failure(in_prog_meta, in_prog_companion)

    # Update dashboard after processing
    if processed > 0:
        update_dashboard()

    return processed


def main() -> None:
    """Start the orchestrator loop."""
    if not acquire_lock():
        logger.error(
            "Another orchestrator is already running. Exiting. "
            "If this is wrong, delete %s",
            str(ORCHESTRATOR_LOCK),
        )
        sys.exit(1)

    atexit.register(release_lock)
    logger.info("Orchestrator started (PID %d)", __import__("os").getpid())
    log_action("orchestrator_started", "system")

    try:
        while True:
            count = run_cycle()
            if count > 0:
                logger.info("Cycle complete: %d file(s) processed", count)
            time.sleep(ORCHESTRATOR_POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Orchestrator stopping...")
    finally:
        release_lock()
        log_action("orchestrator_stopped", "system")
        logger.info("Orchestrator stopped.")


if __name__ == "__main__":
    main()
