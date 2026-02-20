"""Tests for src/ralph_loop.py — Gold tier G2 (Ralph Wiggum self-monitor)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.ralph_loop import (
    check_approval_backlog,
    check_quarantine_count,
    check_stale_pending,
    check_stuck_in_progress,
    create_ralph_alert,
    get_system_status,
    run_ralph_checks,
)


# ---------------------------------------------------------------------------
# Stuck in In_Progress
# ---------------------------------------------------------------------------

class TestCheckStuckInProgress:
    def test_empty_in_progress(self, vault):
        result = check_stuck_in_progress(timeout_minutes=1)
        assert result == []

    def test_recent_file_not_stuck(self, vault):
        ip = vault["IN_PROGRESS"]
        f = ip / "FILE_20260218_120000_doc.md"
        f.write_text(
            "---\noriginal_name: doc.pdf\nsource: file_drop\nstatus: in_progress\n---\n"
        )
        # File just created — should NOT be stuck with 60 minute timeout
        result = check_stuck_in_progress(timeout_minutes=60)
        assert result == []

    def test_old_file_is_stuck(self, vault):
        import os, time
        ip = vault["IN_PROGRESS"]
        f = ip / "FILE_20260218_120000_stuck.md"
        f.write_text(
            "---\noriginal_name: stuck.pdf\nsource: gmail\nstatus: in_progress\n---\n"
        )
        # Force old mtime
        old_time = time.time() - 7200  # 2 hours ago
        os.utime(str(f), (old_time, old_time))
        result = check_stuck_in_progress(timeout_minutes=15)
        assert len(result) == 1
        assert result[0]["original_name"] == "stuck.pdf"
        assert result[0]["age_minutes"] >= 100

    def test_stuck_includes_source(self, vault):
        import os, time
        ip = vault["IN_PROGRESS"]
        f = ip / "FILE_20260218_120000_wa.md"
        f.write_text(
            "---\noriginal_name: wa.pdf\nsource: whatsapp\nstatus: in_progress\n---\n"
        )
        old_time = time.time() - 3600
        os.utime(str(f), (old_time, old_time))
        result = check_stuck_in_progress(timeout_minutes=1)
        assert result[0]["source"] == "whatsapp"


# ---------------------------------------------------------------------------
# Quarantine count
# ---------------------------------------------------------------------------

class TestCheckQuarantineCount:
    def test_empty_quarantine(self, vault):
        result = check_quarantine_count(threshold=3)
        assert result["count"] == 0
        assert result["alert"] is False

    def test_below_threshold(self, vault):
        q = vault["QUARANTINE"]
        (q / "FILE_001.md").write_text("---\noriginal_name: a.pdf\n---\n")
        result = check_quarantine_count(threshold=3)
        assert result["count"] == 1
        assert result["alert"] is False

    def test_at_threshold_triggers_alert(self, vault):
        q = vault["QUARANTINE"]
        for i in range(3):
            (q / f"FILE_00{i}.md").write_text(f"---\noriginal_name: f{i}.pdf\n---\n")
        result = check_quarantine_count(threshold=3)
        assert result["count"] == 3
        assert result["alert"] is True

    def test_reason_files_excluded(self, vault):
        q = vault["QUARANTINE"]
        (q / "file.pdf.reason.md").write_text("reason content")
        result = check_quarantine_count(threshold=1)
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# Approval backlog
# ---------------------------------------------------------------------------

class TestCheckApprovalBacklog:
    def test_empty_backlog(self, vault):
        result = check_approval_backlog(threshold=5)
        assert result["count"] == 0
        assert result["alert"] is False

    def test_small_backlog_no_alert(self, vault):
        pa = vault["PENDING_APPROVAL"]
        (pa / "FILE_001.md").write_text("---\nstatus: pending_approval\n---\n")
        result = check_approval_backlog(threshold=5)
        assert result["alert"] is False

    def test_large_backlog_triggers_alert(self, vault):
        pa = vault["PENDING_APPROVAL"]
        for i in range(6):
            (pa / f"FILE_00{i}.md").write_text("---\nstatus: pending_approval\n---\n")
        result = check_approval_backlog(threshold=5)
        assert result["alert"] is True


# ---------------------------------------------------------------------------
# Stale pending
# ---------------------------------------------------------------------------

class TestCheckStalePending:
    def test_empty_needs_action(self, vault):
        result = check_stale_pending(max_age_hours=2)
        assert result == []

    def test_recent_item_not_stale(self, vault):
        na = vault["NEEDS_ACTION"]
        now_str = datetime.now(timezone.utc).isoformat()
        f = na / "FILE_20260218_120000_fresh.md"
        f.write_text(
            f"---\noriginal_name: fresh.pdf\nsource: file_drop\n"
            f"queued_at: {now_str}\nstatus: pending\n---\n"
        )
        result = check_stale_pending(max_age_hours=2)
        assert result == []

    def test_old_item_is_stale(self, vault):
        na = vault["NEEDS_ACTION"]
        old_str = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        f = na / "FILE_20260218_120000_old.md"
        f.write_text(
            f"---\noriginal_name: old.pdf\nsource: gmail\n"
            f"queued_at: {old_str}\nstatus: pending\n---\n"
        )
        result = check_stale_pending(max_age_hours=2)
        assert len(result) == 1
        assert result[0]["original_name"] == "old.pdf"

    def test_non_pending_excluded(self, vault):
        na = vault["NEEDS_ACTION"]
        old_str = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        f = na / "FILE_20260218_120000_inprog.md"
        f.write_text(
            f"---\noriginal_name: inprog.pdf\nsource: file_drop\n"
            f"queued_at: {old_str}\nstatus: in_progress\n---\n"
        )
        result = check_stale_pending(max_age_hours=2)
        assert result == []


# ---------------------------------------------------------------------------
# Alert creation
# ---------------------------------------------------------------------------

class TestCreateRalphAlert:
    def test_creates_alert_file(self, vault):
        path = create_ralph_alert("test_alert", "Something went wrong.")
        assert path.exists()
        assert "RALPH_" in path.name

    def test_alert_frontmatter(self, vault):
        path = create_ralph_alert("test_alert", "Details here.", severity="critical")
        content = path.read_text()
        assert "type: ralph_alert" in content
        assert "alert_type: test_alert" in content
        assert "severity: critical" in content

    def test_alert_has_recommendation(self, vault):
        path = create_ralph_alert("stuck_in_progress", "Stuck files found.")
        content = path.read_text()
        assert "Recommended Action" in content
        assert "orchestrator" in content.lower()


# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------

class TestRunRalphChecks:
    def test_clean_system_no_alerts(self, vault):
        alerts = run_ralph_checks(
            stuck_timeout_minutes=60,
            quarantine_threshold=10,
            approval_threshold=10,
            stale_hours=24,
        )
        assert alerts == []

    def test_quarantine_alert_fired(self, vault):
        q = vault["QUARANTINE"]
        for i in range(3):
            (q / f"FILE_00{i}.md").write_text(f"---\noriginal_name: f{i}.pdf\n---\n")
        alerts = run_ralph_checks(
            stuck_timeout_minutes=60,
            quarantine_threshold=3,
            approval_threshold=10,
            stale_hours=24,
        )
        assert len(alerts) >= 1
        assert any("quarantine" in str(a) for a in alerts)


# ---------------------------------------------------------------------------
# System status
# ---------------------------------------------------------------------------

class TestGetSystemStatus:
    def test_clean_status(self, vault):
        status = get_system_status()
        assert status["status"] == "ok"
        assert status["issues"] == 0

    def test_quarantine_triggers_warning(self, vault):
        q = vault["QUARANTINE"]
        for i in range(5):
            (q / f"FILE_00{i}.md").write_text(f"---\noriginal_name: f{i}.pdf\n---\n")
        status = get_system_status()
        assert status["status"] == "warning"
        assert status["quarantine_count"] == 5
