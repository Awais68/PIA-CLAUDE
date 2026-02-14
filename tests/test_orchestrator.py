"""Tests for src/orchestrator.py — frontmatter, claim, done, failure, cycle."""

from pathlib import Path
from unittest.mock import patch

from src.orchestrator import (
    _find_companion,
    _read_frontmatter,
    _update_frontmatter,
    claim_file,
    handle_failure,
    move_to_done,
    run_cycle,
)


class TestReadFrontmatter:
    def test_parses_valid_frontmatter(self, sample_md):
        fm = _read_frontmatter(sample_md)
        assert fm["status"] == "pending"
        assert fm["original_name"] == "report.pdf"
        assert fm["retry_count"] == "0"
        assert fm["content_hash"] == "abc123"

    def test_returns_empty_on_no_frontmatter(self, tmp_path):
        f = tmp_path / "no_fm.md"
        f.write_text("Just plain text, no frontmatter.")
        assert _read_frontmatter(f) == {}

    def test_handles_colons_in_values(self, tmp_path):
        f = tmp_path / "colon.md"
        f.write_text("---\nqueued_at: 2026-02-14T12:00:00+00:00\n---\n")
        fm = _read_frontmatter(f)
        assert fm["queued_at"] == "2026-02-14T12:00:00+00:00"


class TestUpdateFrontmatter:
    def test_updates_existing_key(self, sample_md):
        _update_frontmatter(sample_md, {"status": "in_progress"})
        fm = _read_frontmatter(sample_md)
        assert fm["status"] == "in_progress"

    def test_adds_new_key(self, sample_md):
        _update_frontmatter(sample_md, {"new_key": "new_val"})
        fm = _read_frontmatter(sample_md)
        assert fm["new_key"] == "new_val"

    def test_preserves_other_keys(self, sample_md):
        _update_frontmatter(sample_md, {"status": "done"})
        fm = _read_frontmatter(sample_md)
        assert fm["original_name"] == "report.pdf"
        assert fm["content_hash"] == "abc123"

    def test_updates_multiple_keys(self, sample_md):
        _update_frontmatter(sample_md, {"status": "done", "retry_count": "2"})
        fm = _read_frontmatter(sample_md)
        assert fm["status"] == "done"
        assert fm["retry_count"] == "2"


class TestFindCompanion:
    def test_finds_companion_file(self, vault, sample_md, sample_companion):
        companion = _find_companion(sample_md, vault["NEEDS_ACTION"])
        assert companion is not None
        assert companion.name == "FILE_20260214_120000_report.pdf"

    def test_returns_none_when_no_companion(self, vault, sample_md):
        companion = _find_companion(sample_md, vault["NEEDS_ACTION"])
        assert companion is None

    def test_ignores_md_as_companion(self, vault, sample_md):
        # The .md itself has the same stem — should not be returned
        companion = _find_companion(sample_md, vault["NEEDS_ACTION"])
        assert companion is None or companion.suffix != ".md"


class TestClaimFile:
    def test_moves_to_in_progress(self, vault, sample_md, sample_companion):
        new_meta, new_comp = claim_file(sample_md)

        assert new_meta.parent == vault["IN_PROGRESS"]
        assert new_comp is not None
        assert new_comp.parent == vault["IN_PROGRESS"]
        assert not sample_md.exists()

    def test_updates_status_to_in_progress(self, vault, sample_md, sample_companion):
        new_meta, _ = claim_file(sample_md)
        fm = _read_frontmatter(new_meta)
        assert fm["status"] == "in_progress"

    def test_works_without_companion(self, vault, sample_md):
        new_meta, new_comp = claim_file(sample_md)
        assert new_meta.parent == vault["IN_PROGRESS"]
        assert new_comp is None


class TestMoveToDone:
    def test_moves_files_to_done(self, vault, sample_md, sample_companion):
        meta, comp = claim_file(sample_md)
        move_to_done(meta, comp)

        assert not meta.exists()
        done_mds = list(vault["DONE"].glob("FILE_*.md"))
        assert len(done_mds) == 1

        fm = _read_frontmatter(done_mds[0])
        assert fm["status"] == "done"
        assert "processed_at" in fm

    def test_works_without_companion(self, vault, sample_md):
        meta, comp = claim_file(sample_md)
        move_to_done(meta, comp)

        done_mds = list(vault["DONE"].glob("FILE_*.md"))
        assert len(done_mds) == 1


class TestHandleFailure:
    def test_retries_by_moving_back(self, vault, sample_md, sample_companion):
        meta, comp = claim_file(sample_md)
        handle_failure(meta, comp)

        # Should be back in Needs_Action
        retried = list(vault["NEEDS_ACTION"].glob("FILE_*.md"))
        assert len(retried) == 1
        fm = _read_frontmatter(retried[0])
        assert fm["status"] == "pending"
        assert fm["retry_count"] == "1"

    def test_quarantines_after_max_retries(self, vault, sample_md, sample_companion, monkeypatch):
        monkeypatch.setattr("src.orchestrator.MAX_RETRIES", 1)
        meta, comp = claim_file(sample_md)

        # The retry_count starts at 0, incrementing to 1 hits the MAX_RETRIES=1 threshold
        handle_failure(meta, comp)

        quarantined = list(vault["QUARANTINE"].glob("FILE_*.md"))
        assert len(quarantined) == 1
        fm = _read_frontmatter(quarantined[0])
        assert fm["status"] == "quarantined"


class TestRunCycle:
    def test_returns_zero_when_empty(self, vault):
        assert run_cycle() == 0

    def test_processes_pending_file(self, vault, sample_md, sample_companion):
        with patch("src.orchestrator.process_with_claude", return_value=True), \
             patch("src.orchestrator.update_dashboard"):
            count = run_cycle()

        assert count == 1
        done_mds = list(vault["DONE"].glob("FILE_*.md"))
        assert len(done_mds) == 1

    def test_handles_claude_failure(self, vault, sample_md, sample_companion):
        with patch("src.orchestrator.process_with_claude", return_value=False), \
             patch("src.orchestrator.update_dashboard"):
            count = run_cycle()

        assert count == 0
        # File should be back in Needs_Action with incremented retry
        retried = list(vault["NEEDS_ACTION"].glob("FILE_*.md"))
        assert len(retried) == 1

    def test_respects_max_batch_size(self, vault, monkeypatch):
        monkeypatch.setattr("src.orchestrator.MAX_BATCH_SIZE", 1)

        # Create 2 pending files
        for i in range(2):
            md = vault["NEEDS_ACTION"] / f"FILE_2026021{i}_120000_doc{i}.md"
            md.write_text(
                f"---\nstatus: pending\nretry_count: 0\noriginal_name: doc{i}.pdf\n---\n",
                encoding="utf-8",
            )
            comp = vault["NEEDS_ACTION"] / f"FILE_2026021{i}_120000_doc{i}.pdf"
            comp.write_bytes(b"content")

        with patch("src.orchestrator.process_with_claude", return_value=True), \
             patch("src.orchestrator.update_dashboard"):
            count = run_cycle()

        # Only 1 should be processed due to batch size
        assert count == 1

    def test_skips_non_pending(self, vault, sample_md, sample_companion):
        _update_frontmatter(sample_md, {"status": "in_progress"})

        with patch("src.orchestrator.process_with_claude", return_value=True), \
             patch("src.orchestrator.update_dashboard"):
            count = run_cycle()

        assert count == 0
