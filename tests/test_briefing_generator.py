"""Tests for src/briefing_generator.py — Gold tier G1."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.briefing_generator import (
    _collect_done_in_period,
    _collect_pending,
    _collect_quarantine,
    _compute_health_score,
    _count,
    _source_breakdown,
    _type_breakdown,
    generate_briefing,
    get_latest_briefing,
    list_briefings,
)


class TestCountHelper:
    def test_empty_folder(self, tmp_path):
        assert _count(tmp_path) == 0

    def test_counts_files(self, tmp_path):
        (tmp_path / "a.md").write_text("x")
        (tmp_path / "b.md").write_text("x")
        assert _count(tmp_path) == 2

    def test_ignores_gitkeep(self, tmp_path):
        (tmp_path / ".gitkeep").write_text("")
        (tmp_path / "real.md").write_text("x")
        assert _count(tmp_path) == 1

    def test_nonexistent_folder(self, tmp_path):
        assert _count(tmp_path / "missing") == 0


class TestCollectDoneInPeriod:
    def test_empty_done(self, vault):
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = _collect_done_in_period(since)
        assert result == []

    def test_collects_recent_items(self, vault):
        done = vault["DONE"]
        now = datetime.now(timezone.utc)
        f = done / "FILE_20260218_120000_invoice.md"
        f.write_text(
            f"---\noriginal_name: invoice.pdf\ntype: invoice\nsource: gmail\n"
            f"priority: high\nprocessed_at: {now.isoformat()}\nstatus: done\n---\n"
        )
        since = now - timedelta(hours=1)
        items = _collect_done_in_period(since)
        assert len(items) == 1
        assert items[0]["name"] == "invoice.pdf"

    def test_excludes_old_items(self, vault):
        done = vault["DONE"]
        old_time = datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
        f = done / "FILE_20200101_000000_old.md"
        f.write_text(
            f"---\noriginal_name: old.pdf\ntype: other\nsource: file_drop\n"
            f"priority: low\nprocessed_at: {old_time}\nstatus: done\n---\n"
        )
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        items = _collect_done_in_period(since)
        assert items == []


class TestCollectPending:
    def test_empty_needs_action(self, vault):
        result = _collect_pending()
        assert result == []

    def test_collects_pending_files(self, vault):
        na = vault["NEEDS_ACTION"]
        f = na / "FILE_20260218_120000_doc.md"
        f.write_text(
            "---\noriginal_name: doc.pdf\ntype: contract\nsource: file_drop\n"
            "priority: high\nqueued_at: 2026-02-18T12:00:00\nstatus: pending\n---\n"
        )
        items = _collect_pending()
        assert len(items) == 1
        assert items[0]["name"] == "doc.pdf"

    def test_excludes_in_progress(self, vault):
        na = vault["NEEDS_ACTION"]
        f = na / "FILE_20260218_120000_doc.md"
        f.write_text(
            "---\noriginal_name: doc.pdf\ntype: contract\nsource: file_drop\n"
            "priority: high\nqueued_at: 2026-02-18T12:00:00\nstatus: in_progress\n---\n"
        )
        items = _collect_pending()
        assert items == []


class TestCollectQuarantine:
    def test_empty_quarantine(self, vault):
        result = _collect_quarantine()
        assert result == []

    def test_collects_quarantined(self, vault):
        q = vault["QUARANTINE"]
        f = q / "FILE_20260218_120000_bad.md"
        f.write_text(
            "---\noriginal_name: bad.pdf\nreason: Failed after 3 attempts\n"
            "retry_count: 3\nstatus: quarantined\n---\n"
        )
        items = _collect_quarantine()
        assert len(items) == 1
        assert "bad.pdf" in items[0]["name"]

    def test_ignores_reason_files(self, vault):
        q = vault["QUARANTINE"]
        (q / "bad.pdf.reason.md").write_text("reason file")
        items = _collect_quarantine()
        assert items == []


class TestBreakdowns:
    def test_source_breakdown(self):
        items = [
            {"source": "gmail"},
            {"source": "gmail"},
            {"source": "whatsapp"},
            {"source": "file_drop"},
        ]
        counts = _source_breakdown(items)
        assert counts["gmail"] == 2
        assert counts["whatsapp"] == 1
        assert counts["file_drop"] == 1

    def test_type_breakdown(self):
        items = [
            {"type": "invoice"},
            {"type": "invoice"},
            {"type": "contract"},
        ]
        counts = _type_breakdown(items)
        assert counts["invoice"] == 2
        assert counts["contract"] == 1


class TestHealthScore:
    def test_perfect_health(self):
        score = _compute_health_score(
            {"In_Progress": 0, "Needs_Action": 0},
            quarantine_items=[],
            approval_items=[],
        )
        assert score == 100

    def test_quarantine_penalizes(self):
        score = _compute_health_score(
            {"In_Progress": 0, "Needs_Action": 0},
            quarantine_items=[{"name": "a"}, {"name": "b"}],
            approval_items=[],
        )
        assert score == 80

    def test_in_progress_penalizes(self):
        score = _compute_health_score(
            {"In_Progress": 2, "Needs_Action": 0},
            quarantine_items=[],
            approval_items=[],
        )
        assert score == 90

    def test_score_clamped_at_zero(self):
        many_quarantine = [{"name": f"q{i}"} for i in range(20)]
        score = _compute_health_score(
            {"In_Progress": 10, "Needs_Action": 50},
            quarantine_items=many_quarantine,
            approval_items=[{"name": f"a{i}"} for i in range(10)],
        )
        assert score == 0


class TestGenerateBriefing:
    def test_generates_daily_briefing(self, vault):
        path = generate_briefing("daily")
        assert path.exists()
        content = path.read_text()
        assert "Daily Briefing" in content
        assert "health_score" in content

    def test_generates_weekly_briefing(self, vault):
        path = generate_briefing("weekly")
        assert path.exists()
        content = path.read_text()
        assert "Weekly Briefing" in content
        assert "Weekly Trends" in content

    def test_briefing_saved_to_briefings_folder(self, vault):
        from src.config import BRIEFINGS
        path = generate_briefing("daily")
        assert path.parent == BRIEFINGS

    def test_briefing_frontmatter(self, vault):
        path = generate_briefing("daily")
        content = path.read_text()
        assert "type: briefing" in content
        assert "period: daily" in content
        assert "generated_at:" in content
        assert "covers_from:" in content


class TestGetLatestBriefing:
    def test_returns_none_when_empty(self, vault):
        result = get_latest_briefing("daily")
        assert result is None

    def test_returns_most_recent(self, vault):
        p1 = generate_briefing("daily")
        import time; time.sleep(0.01)
        p2 = generate_briefing("daily")
        latest = get_latest_briefing("daily")
        assert latest == p2

    def test_list_briefings(self, vault):
        generate_briefing("daily")
        generate_briefing("weekly")
        all_briefings = list_briefings()
        assert len(all_briefings) == 2
