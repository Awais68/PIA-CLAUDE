"""Job Scheduler — lightweight scheduling for Zoya tasks.

Uses threading-based timers for in-process scheduling. For production,
use cron (see scripts/crontab.example).

Jobs:
    - Orchestrator cycle: every ORCHESTRATOR_POLL_INTERVAL seconds
    - Gmail poll: every GMAIL_POLL_INTERVAL seconds
    - LinkedIn post check: configurable (default: daily at 10 AM)
    - Dashboard refresh: after each orchestrator cycle
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.utils import setup_logger

logger = setup_logger("scheduler")


@dataclass
class Job:
    """A scheduled job definition."""
    name: str
    func: callable
    interval_seconds: int
    enabled: bool = True
    last_run: datetime | None = None
    run_count: int = 0
    _timer: threading.Timer | None = field(default=None, repr=False)


class JobScheduler:
    """Simple interval-based job scheduler running in threads."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._running = False

    def add_job(self, name: str, func: callable, interval_seconds: int) -> None:
        """Register a job to run at a fixed interval."""
        self._jobs[name] = Job(name=name, func=func, interval_seconds=interval_seconds)
        logger.info("Job registered: %s (every %ds)", name, interval_seconds)

    def remove_job(self, name: str) -> None:
        """Remove a job by name."""
        if name in self._jobs:
            job = self._jobs.pop(name)
            if job._timer:
                job._timer.cancel()
            logger.info("Job removed: %s", name)

    def start(self) -> None:
        """Start all registered jobs."""
        self._running = True
        logger.info("Scheduler starting with %d job(s)", len(self._jobs))
        for job in self._jobs.values():
            if job.enabled:
                self._schedule_next(job)

    def stop(self) -> None:
        """Stop all running jobs."""
        self._running = False
        for job in self._jobs.values():
            if job._timer:
                job._timer.cancel()
                job._timer = None
        logger.info("Scheduler stopped")

    def _schedule_next(self, job: Job) -> None:
        """Schedule the next execution of a job."""
        if not self._running or not job.enabled:
            return

        def _run_and_reschedule():
            if not self._running:
                return
            try:
                job.func()
                job.last_run = datetime.now(timezone.utc)
                job.run_count += 1
            except Exception as exc:
                logger.error("Job %s failed: %s", job.name, exc)
            self._schedule_next(job)

        job._timer = threading.Timer(job.interval_seconds, _run_and_reschedule)
        job._timer.daemon = True
        job._timer.start()

    def status(self) -> list[dict]:
        """Return status of all registered jobs."""
        return [
            {
                "name": j.name,
                "enabled": j.enabled,
                "interval": j.interval_seconds,
                "last_run": j.last_run.isoformat() if j.last_run else None,
                "run_count": j.run_count,
            }
            for j in self._jobs.values()
        ]

    @property
    def job_count(self) -> int:
        return len(self._jobs)
