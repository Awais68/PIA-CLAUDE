"""Tests for src/scheduler/job_scheduler.py — lightweight job scheduler."""

import time
from unittest.mock import MagicMock

from src.scheduler.job_scheduler import JobScheduler


class TestJobScheduler:
    def test_add_job(self):
        sched = JobScheduler()
        sched.add_job("test", lambda: None, 60)
        assert sched.job_count == 1

    def test_remove_job(self):
        sched = JobScheduler()
        sched.add_job("test", lambda: None, 60)
        sched.remove_job("test")
        assert sched.job_count == 0

    def test_status_empty(self):
        sched = JobScheduler()
        assert sched.status() == []

    def test_status_shows_jobs(self):
        sched = JobScheduler()
        sched.add_job("job1", lambda: None, 30)
        sched.add_job("job2", lambda: None, 60)
        status = sched.status()
        assert len(status) == 2
        names = {s["name"] for s in status}
        assert names == {"job1", "job2"}

    def test_job_runs(self):
        mock_fn = MagicMock()
        sched = JobScheduler()
        sched.add_job("quick_job", mock_fn, 0)  # 0 second interval
        sched.start()
        time.sleep(0.2)
        sched.stop()
        assert mock_fn.call_count >= 1

    def test_stop_halts_jobs(self):
        sched = JobScheduler()
        sched.add_job("test", lambda: None, 1)
        sched.start()
        sched.stop()
        assert not sched._running

    def test_job_error_does_not_crash(self):
        def failing_job():
            raise RuntimeError("oops")

        sched = JobScheduler()
        sched.add_job("fail_job", failing_job, 0)
        sched.start()
        time.sleep(0.2)
        sched.stop()
        # Should not crash — just log the error
