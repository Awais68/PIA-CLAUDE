"""Abstract base class for all Zoya watchers.

Every watcher (file-system, Gmail, WhatsApp, …) inherits from BaseWatcher.
This guarantees a uniform lifecycle: setup → poll loop → teardown, plus
built-in retry logic, health-check reporting, and structured logging.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from src.utils import setup_logger, log_action


class BaseWatcher(ABC):
    """Abstract watcher with retry logic and health-check support."""

    # Subclasses should set a human-readable name
    name: str = "base"

    def __init__(self, poll_interval: int = 60, max_retries: int = 3) -> None:
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.logger = setup_logger(f"watcher.{self.name}")
        self._running = False
        self._consecutive_errors = 0
        self._last_poll: datetime | None = None
        self._total_processed = 0

    # ------------------------------------------------------------------
    # Abstract interface — subclasses MUST implement
    # ------------------------------------------------------------------

    @abstractmethod
    def setup(self) -> None:
        """One-time initialisation (auth, connections, etc.)."""

    @abstractmethod
    def poll(self) -> int:
        """Run one polling cycle. Return count of items ingested."""

    @abstractmethod
    def teardown(self) -> None:
        """Clean-up resources on shutdown."""

    # ------------------------------------------------------------------
    # Concrete lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Run the watcher loop: setup → poll → sleep → repeat."""
        self.logger.info("Starting %s watcher (poll every %ds)", self.name, self.poll_interval)
        self.setup()
        self._running = True

        try:
            while self._running:
                self._run_one_cycle()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            self.logger.info("%s watcher stopped by user", self.name)
        finally:
            self.teardown()
            self.logger.info("%s watcher shut down", self.name)

    def stop(self) -> None:
        """Signal the watcher to stop after the current cycle."""
        self._running = False

    # ------------------------------------------------------------------
    # Retry wrapper
    # ------------------------------------------------------------------

    def _run_one_cycle(self) -> None:
        try:
            count = self.poll()
            self._last_poll = datetime.now(timezone.utc)
            self._total_processed += count
            self._consecutive_errors = 0
            if count > 0:
                self.logger.info("Ingested %d item(s) this cycle", count)
        except Exception as exc:
            self._consecutive_errors += 1
            self.logger.error(
                "%s poll failed (%d/%d): %s",
                self.name,
                self._consecutive_errors,
                self.max_retries,
                exc,
            )
            log_action(
                f"{self.name}_poll_error",
                str(exc),
                {"consecutive_errors": self._consecutive_errors},
                "error",
            )
            if self._consecutive_errors >= self.max_retries:
                self.logger.critical(
                    "%s watcher hit max retries (%d) — stopping",
                    self.name,
                    self.max_retries,
                )
                self._running = False

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health(self) -> dict:
        """Return a health-check dict suitable for a dashboard or API."""
        return {
            "watcher": self.name,
            "running": self._running,
            "last_poll": self._last_poll.isoformat() if self._last_poll else None,
            "total_processed": self._total_processed,
            "consecutive_errors": self._consecutive_errors,
        }
