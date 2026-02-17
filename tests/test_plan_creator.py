"""Tests for Plan.md reasoning loop (S4)."""

from src.orchestrator import (
    _read_frontmatter,
    _update_frontmatter,
    create_plan,
    should_create_plan,
)


class TestShouldCreatePlan:
    def test_invoice_needs_plan(self):
        assert should_create_plan({"type": "invoice"}) is True

    def test_contract_needs_plan(self):
        assert should_create_plan({"type": "contract"}) is True

    def test_proposal_needs_plan(self):
        assert should_create_plan({"type": "proposal"}) is True

    def test_note_no_plan(self):
        assert should_create_plan({"type": "note"}) is False

    def test_other_no_plan(self):
        assert should_create_plan({"type": "other"}) is False

    def test_approval_required_flag(self):
        assert should_create_plan({"type": "email", "approval_required": "true"}) is True

    def test_empty_frontmatter(self):
        assert should_create_plan({}) is False


class TestCreatePlan:
    def test_creates_plan_file(self, vault, sample_md):
        _update_frontmatter(sample_md, {"type": "invoice"})
        fm = _read_frontmatter(sample_md)
        plan = create_plan(sample_md, fm)

        assert plan.exists()
        assert plan.parent == vault["PLANS"]
        assert plan.name.startswith("PLAN_")

    def test_plan_has_frontmatter(self, vault, sample_md):
        _update_frontmatter(sample_md, {"type": "invoice"})
        fm = _read_frontmatter(sample_md)
        plan = create_plan(sample_md, fm)

        plan_fm = _read_frontmatter(plan)
        assert plan_fm["status"] == "draft"
        assert plan_fm["complexity"] == "moderate"
        assert plan_fm["requires_approval"] == "true"

    def test_contract_is_complex(self, vault, sample_md):
        _update_frontmatter(sample_md, {"type": "contract"})
        fm = _read_frontmatter(sample_md)
        plan = create_plan(sample_md, fm)

        plan_fm = _read_frontmatter(plan)
        assert plan_fm["complexity"] == "complex"

    def test_plan_contains_steps(self, vault, sample_md):
        _update_frontmatter(sample_md, {"type": "proposal"})
        fm = _read_frontmatter(sample_md)
        plan = create_plan(sample_md, fm)

        content = plan.read_text()
        assert "## Steps" in content
        assert "## Objective" in content
        assert "[ ]" in content

    def test_plan_references_original(self, vault, sample_md):
        fm = _read_frontmatter(sample_md)
        fm["type"] = "invoice"
        plan = create_plan(sample_md, fm)

        content = plan.read_text()
        assert "report.pdf" in content

    def test_plan_for_generic_type(self, vault, sample_md):
        fm = _read_frontmatter(sample_md)
        fm["type"] = "email"
        fm["approval_required"] = "true"
        plan = create_plan(sample_md, fm)

        plan_fm = _read_frontmatter(plan)
        assert plan_fm["complexity"] == "simple"
