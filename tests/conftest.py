"""Shared fixtures for Zoya tests.

Every test gets its own temporary vault directory so tests never touch
the real AI_Employee_Vault/ and can run fully in parallel.
"""

import pytest
from pathlib import Path


@pytest.fixture()
def vault(tmp_path: Path, monkeypatch):
    """Create an isolated vault directory tree and patch config paths everywhere."""
    import src.config as cfg
    import src.utils as utils_mod
    import src.watcher as watcher_mod
    import src.orchestrator as orch_mod

    dirs = {
        "VAULT_PATH": tmp_path / "vault",
        "INBOX": tmp_path / "vault" / "Inbox",
        "NEEDS_ACTION": tmp_path / "vault" / "Needs_Action",
        "IN_PROGRESS": tmp_path / "vault" / "In_Progress",
        "DONE": tmp_path / "vault" / "Done",
        "QUARANTINE": tmp_path / "vault" / "Quarantine",
        "LOGS": tmp_path / "vault" / "Logs",
    }
    for attr, path in dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(cfg, attr, path)

    dashboard = tmp_path / "vault" / "Dashboard.md"
    lock_path = tmp_path / "orchestrator.lock.pid"

    monkeypatch.setattr(cfg, "DASHBOARD", dashboard)
    monkeypatch.setattr(cfg, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cfg, "ORCHESTRATOR_LOCK", lock_path)

    # Patch the already-imported names in consuming modules so they see
    # the tmp_path versions instead of the real vault.
    for attr, path in dirs.items():
        if hasattr(utils_mod, attr):
            monkeypatch.setattr(utils_mod, attr, path)
        if hasattr(watcher_mod, attr):
            monkeypatch.setattr(watcher_mod, attr, path)
        if hasattr(orch_mod, attr):
            monkeypatch.setattr(orch_mod, attr, path)

    # Patch non-dir constants too
    for mod in (utils_mod, watcher_mod, orch_mod):
        if hasattr(mod, "DASHBOARD"):
            monkeypatch.setattr(mod, "DASHBOARD", dashboard)
        if hasattr(mod, "PROJECT_ROOT"):
            monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
        if hasattr(mod, "ORCHESTRATOR_LOCK"):
            monkeypatch.setattr(mod, "ORCHESTRATOR_LOCK", lock_path)
        if hasattr(mod, "VAULT_PATH"):
            monkeypatch.setattr(mod, "VAULT_PATH", dirs["VAULT_PATH"])

    return dirs


@pytest.fixture()
def sample_pdf(vault, tmp_path: Path):
    """Create a tiny fake PDF in the Inbox."""
    pdf = vault["INBOX"] / "report.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake content for testing")
    return pdf


@pytest.fixture()
def sample_md(vault, tmp_path: Path):
    """Create a sample metadata file in Needs_Action."""
    md = vault["NEEDS_ACTION"] / "FILE_20260214_120000_report.md"
    md.write_text(
        "---\n"
        "type: file_drop\n"
        "original_name: report.pdf\n"
        "queued_name: FILE_20260214_120000_report.pdf\n"
        "size_bytes: 1024\n"
        "content_hash: abc123\n"
        "queued_at: 2026-02-14T12:00:00+00:00\n"
        "status: pending\n"
        "retry_count: 0\n"
        "---\n\nNew file dropped for processing.\n",
        encoding="utf-8",
    )
    return md


@pytest.fixture()
def sample_companion(vault):
    """Create a companion file alongside the sample metadata."""
    companion = vault["NEEDS_ACTION"] / "FILE_20260214_120000_report.pdf"
    companion.write_bytes(b"%PDF-1.4 fake content")
    return companion
