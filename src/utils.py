"""Shared utilities: locking, logging, hashing."""

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.config import LOGS, ORCHESTRATOR_LOCK

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger(name: str) -> logging.Logger:
    """Create a logger that writes to stdout and the daily log file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # stdout
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # daily file
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = LOGS / f"{today}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# ---------------------------------------------------------------------------
# Structured action log (JSON)
# ---------------------------------------------------------------------------

def log_action(
    action_type: str,
    target: str,
    parameters: dict | None = None,
    result: str = "success",
) -> None:
    """Append a structured JSON log entry for the day."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_file = LOGS / f"{today}.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_type": action_type,
        "actor": "zoya",
        "target": target,
        "parameters": parameters or {},
        "result": result,
    }

    # Append to JSON-lines file (one JSON object per line, easy to parse)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# File-based process lock  (prevents duplicate orchestrator runs)
# ---------------------------------------------------------------------------

def acquire_lock() -> bool:
    """Try to acquire the orchestrator lock. Returns True on success."""
    pid = os.getpid()
    if ORCHESTRATOR_LOCK.exists():
        existing_pid = ORCHESTRATOR_LOCK.read_text().strip()
        # Check if the PID is still alive
        try:
            os.kill(int(existing_pid), 0)
            return False  # process still running
        except (OSError, ValueError):
            pass  # stale lock, take over

    ORCHESTRATOR_LOCK.write_text(str(pid))
    return True


def release_lock() -> None:
    """Release the orchestrator lock."""
    if ORCHESTRATOR_LOCK.exists():
        try:
            stored_pid = ORCHESTRATOR_LOCK.read_text().strip()
            if stored_pid == str(os.getpid()):
                ORCHESTRATOR_LOCK.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Content hashing (deduplication)
# ---------------------------------------------------------------------------

def file_hash(path: Path) -> str:
    """Return SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
