"""Tests for HITL approval workflow (S6)."""

from unittest.mock import patch

from src.orchestrator import (
    _read_frontmatter,
    _update_frontmatter,
    claim_file,
    evaluate_hitl,
    process_approved_files,
    process_file,
    process_rejected_files,
    route_to_approval,
    run_cycle,
)


class TestEvaluateHitl:
    def test_invoice_high_priority_needs_approval(self, vault, sample_md, sample_companion):
        meta, _ = claim_file(sample_md)
        _update_frontmatter(meta, {"type": "invoice", "priority": "high", "status": "done"})
        assert evaluate_hitl(meta) is True

    def test_note_low_priority_no_approval(self, vault, sample_md, sample_companion):
        meta, _ = claim_file(sample_md)
        _update_frontmatter(meta, {"type": "note", "priority": "low", "status": "done"})
        assert evaluate_hitl(meta) is False

    def test_explicit_approval_flag(self, vault, sample_md, sample_companion):
        meta, _ = claim_file(sample_md)
        _update_frontmatter(meta, {"approval_required": "true", "status": "done"})
        assert evaluate_hitl(meta) is True

    def test_gmail_high_priority_needs_approval(self, vault, sample_md, sample_companion):
        meta, _ = claim_file(sample_md)
        _update_frontmatter(meta, {"source": "gmail", "priority": "high", "status": "done"})
        assert evaluate_hitl(meta) is True

    def test_linkedin_post_always_needs_approval(self, vault, sample_md, sample_companion):
        meta, _ = claim_file(sample_md)
        _update_frontmatter(meta, {"type": "linkedin_post", "status": "done"})
        assert evaluate_hitl(meta) is True

    def test_contract_high_needs_approval(self, vault, sample_md, sample_companion):
        meta, _ = claim_file(sample_md)
        _update_frontmatter(meta, {"type": "contract", "priority": "high", "status": "done"})
        assert evaluate_hitl(meta) is True

    def test_receipt_low_no_approval(self, vault, sample_md, sample_companion):
        meta, _ = claim_file(sample_md)
        _update_frontmatter(meta, {"type": "receipt", "priority": "low", "status": "done"})
        assert evaluate_hitl(meta) is False


class TestRouteToApproval:
    def test_file_moved_to_pending_approval(self, vault, sample_md, sample_companion):
        meta, comp = claim_file(sample_md)
        new_meta, new_comp = route_to_approval(meta, comp)

        assert new_meta.parent == vault["PENDING_APPROVAL"]
        assert not meta.exists()
        assert new_comp is not None
        assert new_comp.parent == vault["PENDING_APPROVAL"]

    def test_status_updated_to_pending_approval(self, vault, sample_md, sample_companion):
        meta, comp = claim_file(sample_md)
        new_meta, _ = route_to_approval(meta, comp)

        fm = _read_frontmatter(new_meta)
        assert fm["status"] == "pending_approval"
        assert "approval_requested_at" in fm

    def test_works_without_companion(self, vault, sample_md):
        meta, comp = claim_file(sample_md)
        new_meta, new_comp = route_to_approval(meta, comp)

        assert new_meta.parent == vault["PENDING_APPROVAL"]
        assert new_comp is None


class TestProcessApprovedFiles:
    def test_approved_file_moved_to_done(self, vault, sample_md, sample_companion):
        meta, comp = claim_file(sample_md)
        approval_meta, approval_comp = route_to_approval(meta, comp)

        # Simulate human moving files to Approved/
        import shutil
        done_meta = vault["APPROVED"] / approval_meta.name
        shutil.move(str(approval_meta), done_meta)
        if approval_comp:
            shutil.move(str(approval_comp), vault["APPROVED"] / approval_comp.name)

        count = process_approved_files()
        assert count == 1

        done_mds = list(vault["DONE"].glob("FILE_*.md"))
        assert len(done_mds) == 1
        fm = _read_frontmatter(done_mds[0])
        assert fm["approval_status"] == "approved"
        assert fm["status"] == "done"

    def test_returns_zero_when_empty(self, vault):
        assert process_approved_files() == 0


class TestProcessRejectedFiles:
    def test_rejected_file_moved_to_done(self, vault, sample_md, sample_companion):
        meta, comp = claim_file(sample_md)
        approval_meta, approval_comp = route_to_approval(meta, comp)

        # Simulate human moving files to Rejected/
        import shutil
        rej_meta = vault["REJECTED"] / approval_meta.name
        shutil.move(str(approval_meta), rej_meta)
        if approval_comp:
            shutil.move(str(approval_comp), vault["REJECTED"] / approval_comp.name)

        count = process_rejected_files()
        assert count == 1

        done_mds = list(vault["DONE"].glob("FILE_*.md"))
        assert len(done_mds) == 1
        fm = _read_frontmatter(done_mds[0])
        assert fm["approval_status"] == "rejected"

    def test_returns_zero_when_empty(self, vault):
        assert process_rejected_files() == 0


class TestRunCycleWithHITL:
    def test_existing_bronze_flow_unaffected(self, vault, sample_md, sample_companion):
        """Low-priority notes should go straight to Done (no HITL)."""
        _update_frontmatter(sample_md, {"type": "note", "priority": "low"})

        with patch("src.orchestrator.process_file", return_value=True), \
             patch("src.orchestrator.update_dashboard"):
            count = run_cycle()

        assert count == 1
        done_mds = list(vault["DONE"].glob("FILE_*.md"))
        assert len(done_mds) == 1

    def test_high_priority_invoice_routed_to_approval(self, vault, sample_md, sample_companion):
        """High-priority invoices should be routed to HITL approval."""
        with patch("src.orchestrator.process_file") as mock_process, \
             patch("src.orchestrator.update_dashboard"):
            # Mock process_file to update frontmatter as if AI processed it
            def _fake_process(meta, comp):
                _update_frontmatter(meta, {"type": "invoice", "priority": "high", "status": "done"})
                return True
            mock_process.side_effect = _fake_process
            count = run_cycle()

        assert count == 1
        # File should be in Pending_Approval, not Done
        pending = list(vault["PENDING_APPROVAL"].glob("FILE_*.md"))
        assert len(pending) == 1
        done = list(vault["DONE"].glob("FILE_*.md"))
        assert len(done) == 0
