"""Tests for src/watchers/base_watcher.py — lifecycle, retry, health check."""

from unittest.mock import patch

from src.watchers.base_watcher import BaseWatcher


class ConcreteWatcher(BaseWatcher):
    """Minimal concrete watcher for testing."""

    name = "test"

    def __init__(self, poll_results=None, poll_interval=1, max_retries=3):
        super().__init__(poll_interval=poll_interval, max_retries=max_retries)
        self._poll_results = poll_results or []
        self._poll_index = 0
        self.setup_called = False
        self.teardown_called = False

    def setup(self):
        self.setup_called = True

    def poll(self):
        if self._poll_index >= len(self._poll_results):
            self.stop()
            return 0
        result = self._poll_results[self._poll_index]
        self._poll_index += 1
        if isinstance(result, Exception):
            raise result
        return result

    def teardown(self):
        self.teardown_called = True


class TestBaseWatcherLifecycle:
    def test_setup_and_teardown_called(self):
        w = ConcreteWatcher(poll_results=[])
        with patch("time.sleep"):
            w.start()
        assert w.setup_called
        assert w.teardown_called

    def test_processes_items(self):
        w = ConcreteWatcher(poll_results=[3, 2])
        with patch("time.sleep"):
            w.start()
        assert w._total_processed == 5

    def test_stop_halts_loop(self):
        w = ConcreteWatcher(poll_results=[1])
        with patch("time.sleep"):
            w.start()
        assert not w._running


class TestBaseWatcherRetry:
    def test_increments_error_count(self):
        # After the error, poll returns 0 (stop), which resets the counter.
        # So we use max_retries=1 to stop immediately on the first error.
        w = ConcreteWatcher(poll_results=[RuntimeError("fail")], max_retries=1)
        with patch("time.sleep"):
            w.start()
        assert w._consecutive_errors == 1

    def test_resets_errors_on_success(self):
        # Error first, then success (which resets counter), then stop
        w = ConcreteWatcher(poll_results=[RuntimeError("fail"), 1])
        with patch("time.sleep"):
            w.start()
        assert w._consecutive_errors == 0

    def test_stops_after_max_retries(self):
        errors = [RuntimeError("fail")] * 3
        w = ConcreteWatcher(poll_results=errors, max_retries=3)
        with patch("time.sleep"):
            w.start()
        assert w._consecutive_errors == 3
        assert not w._running


class TestBaseWatcherHealth:
    def test_health_before_start(self):
        w = ConcreteWatcher()
        h = w.health()
        assert h["watcher"] == "test"
        assert h["running"] is False
        assert h["last_poll"] is None
        assert h["total_processed"] == 0

    def test_health_after_processing(self):
        w = ConcreteWatcher(poll_results=[5])
        with patch("time.sleep"):
            w.start()
        h = w.health()
        assert h["total_processed"] == 5
        assert h["last_poll"] is not None
        assert h["consecutive_errors"] == 0
