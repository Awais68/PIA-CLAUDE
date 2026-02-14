"""Tests for src/config.py — verify all constants are sane."""

from pathlib import Path

from src.config import (
    DASHBOARD,
    DONE,
    FILE_STABILITY_CHECKS,
    FILE_STABILITY_WAIT,
    IN_PROGRESS,
    INBOX,
    LOGS,
    MAX_BATCH_SIZE,
    MAX_FILE_SIZE_MB,
    MAX_RETRIES,
    NEEDS_ACTION,
    ORCHESTRATOR_LOCK,
    ORCHESTRATOR_POLL_INTERVAL,
    PROJECT_ROOT,
    QUARANTINE,
    SUPPORTED_EXTENSIONS,
    VAULT_PATH,
    WATCHER_POLL_INTERVAL,
)


class TestPaths:
    def test_project_root_is_directory(self):
        assert PROJECT_ROOT.is_dir()

    def test_vault_under_project_root(self):
        assert VAULT_PATH.parent == PROJECT_ROOT

    def test_all_vault_subdirs_under_vault(self):
        for d in (INBOX, NEEDS_ACTION, IN_PROGRESS, DONE, QUARANTINE, LOGS):
            assert d.parent == VAULT_PATH

    def test_dashboard_is_md(self):
        assert DASHBOARD.suffix == ".md"

    def test_lock_file_under_project_root(self):
        assert ORCHESTRATOR_LOCK.parent == PROJECT_ROOT


class TestWatcherSettings:
    def test_supported_extensions_non_empty(self):
        assert len(SUPPORTED_EXTENSIONS) > 0

    def test_supported_extensions_are_dotted(self):
        for ext in SUPPORTED_EXTENSIONS:
            assert ext.startswith(".")

    def test_pdf_supported(self):
        assert ".pdf" in SUPPORTED_EXTENSIONS

    def test_stability_wait_positive(self):
        assert FILE_STABILITY_WAIT > 0

    def test_stability_checks_positive(self):
        assert FILE_STABILITY_CHECKS >= 1

    def test_max_file_size_positive(self):
        assert MAX_FILE_SIZE_MB > 0

    def test_poll_interval_positive(self):
        assert WATCHER_POLL_INTERVAL > 0


class TestOrchestratorSettings:
    def test_poll_interval_positive(self):
        assert ORCHESTRATOR_POLL_INTERVAL > 0

    def test_max_batch_size_positive(self):
        assert MAX_BATCH_SIZE >= 1

    def test_max_retries_positive(self):
        assert MAX_RETRIES >= 1
