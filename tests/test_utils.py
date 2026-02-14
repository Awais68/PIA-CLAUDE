"""Tests for src/utils.py — logging, locking, hashing."""

import json
import os
from pathlib import Path

from src.utils import acquire_lock, file_hash, log_action, release_lock, setup_logger


class TestSetupLogger:
    def test_returns_logger(self, vault):
        logger = setup_logger("test_logger_unique1")
        assert logger.name == "test_logger_unique1"

    def test_has_handlers(self, vault):
        logger = setup_logger("test_logger_unique2")
        assert len(logger.handlers) >= 2  # stdout + file

    def test_idempotent(self, vault):
        l1 = setup_logger("test_logger_unique3")
        n = len(l1.handlers)
        l2 = setup_logger("test_logger_unique3")
        assert l1 is l2
        assert len(l2.handlers) == n

    def test_creates_log_file(self, vault):
        setup_logger("test_logger_unique4")
        log_files = list(vault["LOGS"].glob("*.log"))
        assert len(log_files) >= 1


class TestLogAction:
    def test_creates_json_log(self, vault):
        log_action("test_action", "/some/target", {"key": "val"})
        json_files = list(vault["LOGS"].glob("*.json"))
        assert len(json_files) == 1
        lines = json_files[0].read_text().strip().splitlines()
        entry = json.loads(lines[-1])
        assert entry["action_type"] == "test_action"
        assert entry["target"] == "/some/target"
        assert entry["parameters"]["key"] == "val"
        assert entry["actor"] == "zoya"
        assert entry["result"] == "success"

    def test_appends_multiple_entries(self, vault):
        log_action("a1", "t1")
        log_action("a2", "t2")
        json_files = list(vault["LOGS"].glob("*.json"))
        lines = json_files[0].read_text().strip().splitlines()
        assert len(lines) == 2


class TestLock:
    def test_acquire_and_release(self, vault, monkeypatch):
        import src.config as cfg
        lock_path = cfg.ORCHESTRATOR_LOCK

        assert acquire_lock() is True
        assert lock_path.exists()
        assert lock_path.read_text().strip() == str(os.getpid())

        release_lock()
        assert not lock_path.exists()

    def test_acquire_fails_if_pid_alive(self, vault, monkeypatch):
        import src.config as cfg
        lock_path = cfg.ORCHESTRATOR_LOCK

        # Write our own PID — os.kill(our_pid, 0) will succeed
        lock_path.write_text(str(os.getpid()))
        assert acquire_lock() is False

        # Cleanup
        lock_path.unlink()

    def test_acquire_succeeds_on_stale_lock(self, vault, monkeypatch):
        import src.config as cfg
        lock_path = cfg.ORCHESTRATOR_LOCK

        # PID 99999999 almost certainly doesn't exist
        lock_path.write_text("99999999")
        assert acquire_lock() is True

        release_lock()

    def test_release_only_own_lock(self, vault, monkeypatch):
        import src.config as cfg
        lock_path = cfg.ORCHESTRATOR_LOCK

        lock_path.write_text("99999999")  # another PID
        release_lock()  # should NOT remove it
        assert lock_path.exists()

        # Cleanup
        lock_path.unlink()


class TestFileHash:
    def test_deterministic(self, tmp_path: Path):
        f = tmp_path / "a.txt"
        f.write_text("hello world")
        assert file_hash(f) == file_hash(f)

    def test_different_content_different_hash(self, tmp_path: Path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("hello")
        f2.write_text("world")
        assert file_hash(f1) != file_hash(f2)

    def test_returns_hex_string(self, tmp_path: Path):
        f = tmp_path / "a.txt"
        f.write_text("test")
        h = file_hash(f)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex
        int(h, 16)  # should not raise
