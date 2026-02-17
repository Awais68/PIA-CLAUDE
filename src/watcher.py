"""
File System Watcher for Zoya.

Monitors AI_Employee_Vault/Inbox/ for new files and creates metadata
entries in Needs_Action/ for the orchestrator to pick up.

Edge cases handled:
  - File stability: waits until file size stops changing before copying.
  - File type filtering: only .pdf, .docx, .md are accepted.
  - Deduplication: content-hashes prevent processing the same file twice.
  - Timestamped names: prevents filename collisions.
  - OS junk filtering: ignores .DS_Store, thumbs.db, temp files.
  - Max file size: rejects files over the configured limit.
  - Crash recovery: stateless — safe to restart at any time.
"""

import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.config import (
    FILE_STABILITY_CHECKS,
    FILE_STABILITY_WAIT,
    INBOX,
    MAX_FILE_SIZE_MB,
    NEEDS_ACTION,
    QUARANTINE,
    SUPPORTED_EXTENSIONS,
    WATCHER_POLL_INTERVAL,
)
from src.utils import file_hash, log_action, setup_logger

logger = setup_logger("watcher")

# Files the OS may silently create — always ignore
JUNK_PATTERNS = {".ds_store", "thumbs.db", "desktop.ini", ".gitkeep"}


class InboxHandler(FileSystemEventHandler):
    """Watches /Inbox/ and creates metadata in /Needs_Action/."""

    def __init__(self) -> None:
        super().__init__()
        self._seen_hashes: set[str] = set()
        # Pre-populate hashes from existing Needs_Action files to avoid
        # re-processing on watcher restart.
        self._load_existing_hashes()

    def _load_existing_hashes(self) -> None:
        """Scan Needs_Action for previously recorded content hashes."""
        for md_file in NEEDS_ACTION.glob("FILE_*.md"):
            try:
                text = md_file.read_text(encoding="utf-8")
                for line in text.splitlines():
                    if line.startswith("content_hash:"):
                        h = line.split(":", 1)[1].strip()
                        self._seen_hashes.add(h)
                        break
            except OSError:
                pass

    # ---- watchdog callback -----------------------------------------------

    def on_created(self, event) -> None:  # noqa: ANN001
        if event.is_directory:
            return
        source = Path(event.src_path)
        try:
            self._handle_new_file(source)
        except Exception:
            logger.exception("Failed to handle %s", source.name)

    # ---- pipeline --------------------------------------------------------

    def _handle_new_file(self, source: Path) -> None:
        # 1. Ignore OS junk
        if source.name.lower() in JUNK_PATTERNS or source.name.startswith("~"):
            logger.debug("Ignoring junk file: %s", source.name)
            return

        # 2. Filter unsupported extensions
        if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.warning(
                "Unsupported file type '%s' — moving to Quarantine", source.suffix
            )
            self._quarantine(source, reason=f"Unsupported file type: {source.suffix}")
            return

        # 3. Wait for file stability (large copies may still be writing)
        if not self._wait_for_stable(source):
            logger.warning("File never stabilised: %s — quarantining", source.name)
            self._quarantine(source, reason="File never finished writing")
            return

        # 4. Check file size
        size_mb = source.stat().st_size / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            logger.warning(
                "File too large (%.1f MB > %d MB limit): %s",
                size_mb,
                MAX_FILE_SIZE_MB,
                source.name,
            )
            self._quarantine(
                source, reason=f"File too large: {size_mb:.1f} MB (limit {MAX_FILE_SIZE_MB} MB)"
            )
            return

        # 5. Deduplication via content hash
        content_hash = file_hash(source)
        if content_hash in self._seen_hashes:
            logger.info("Duplicate file detected (hash match), skipping: %s", source.name)
            # Remove the duplicate from Inbox so it doesn't pile up
            source.unlink(missing_ok=True)
            return
        self._seen_hashes.add(content_hash)

        # 6. Move file + create metadata with timestamped name
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        safe_stem = self._sanitise_name(source.stem)
        dest_name = f"FILE_{ts}_{safe_stem}{source.suffix}"
        meta_name = f"FILE_{ts}_{safe_stem}.md"

        dest_path = NEEDS_ACTION / dest_name
        meta_path = NEEDS_ACTION / meta_name

        # Move instead of copy+delete — atomic and avoids race conditions
        shutil.move(str(source), dest_path)
        self._write_metadata(meta_path, source, dest_path, content_hash)

        logger.info("Queued for processing: %s -> %s", source.name, dest_name)
        log_action("file_queued", str(dest_path), {"original": source.name})

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _wait_for_stable(path: Path) -> bool:
        """Poll file size until it stops changing."""
        prev_size = -1
        stable_count = 0
        for _ in range(30):  # max 30 * WAIT = 60s timeout
            if not path.exists():
                return False
            size = path.stat().st_size
            if size == prev_size and size > 0:
                stable_count += 1
                if stable_count >= FILE_STABILITY_CHECKS:
                    return True
            else:
                stable_count = 0
            prev_size = size
            time.sleep(FILE_STABILITY_WAIT)
        return False

    @staticmethod
    def _sanitise_name(name: str) -> str:
        """Replace problematic characters in filenames."""
        keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        return "".join(c if c in keep else "_" for c in name).strip("_")[:80]

    @staticmethod
    def _write_metadata(
        meta_path: Path, source: Path, dest: Path, content_hash: str
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        size_bytes = dest.stat().st_size
        content = f"""---
type: file_drop
original_name: {source.name}
queued_name: {dest.name}
size_bytes: {size_bytes}
content_hash: {content_hash}
queued_at: {now}
status: pending
retry_count: 0
---

New file dropped for processing.
"""
        meta_path.write_text(content, encoding="utf-8")

    @staticmethod
    def _quarantine(source: Path, reason: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        q_path = QUARANTINE / f"Q_{ts}_{source.name}"
        shutil.move(str(source), q_path)
        # Write a reason file alongside
        reason_path = q_path.with_suffix(q_path.suffix + ".reason.md")
        reason_path.write_text(
            f"---\nquarantined_at: {datetime.now(timezone.utc).isoformat()}\n"
            f"reason: {reason}\noriginal_name: {source.name}\n---\n",
            encoding="utf-8",
        )
        log_action("file_quarantined", str(q_path), {"reason": reason})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the file system watcher."""
    # Ensure directories exist
    INBOX.mkdir(parents=True, exist_ok=True)
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    QUARANTINE.mkdir(parents=True, exist_ok=True)

    handler = InboxHandler()
    observer = Observer()
    observer.schedule(handler, str(INBOX), recursive=False)
    observer.start()
    logger.info("Watcher started — monitoring %s", INBOX)

    try:
        while True:
            time.sleep(WATCHER_POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Watcher stopping...")
    finally:
        observer.stop()
        observer.join()
        logger.info("Watcher stopped.")


if __name__ == "__main__":
    main()
