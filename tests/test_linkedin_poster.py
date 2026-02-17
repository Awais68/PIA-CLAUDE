"""Tests for src/linkedin_poster.py — LinkedIn auto-posting (S3)."""

from unittest.mock import patch

from src.linkedin_poster import (
    create_approval_request,
    generate_post_content,
    post_to_linkedin,
    process_approved_posts,
)


class TestGeneratePostContent:
    def test_returns_string(self):
        result = generate_post_content("New product launch!")
        assert isinstance(result, str)
        assert "New product launch!" in result

    def test_truncates_long_content(self):
        long_topic = "x" * 2000
        result = generate_post_content(long_topic)
        assert len(result) <= 1300

    def test_includes_context(self):
        result = generate_post_content("Launch", "Q1 revenue up 20%")
        assert "Q1 revenue up 20%" in result


class TestCreateApprovalRequest:
    def test_creates_file_in_pending(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.linkedin_poster.PENDING_APPROVAL", tmp_path)

        path = create_approval_request("Great update!", "#business")
        assert path.exists()
        assert path.parent == tmp_path

    def test_file_has_correct_frontmatter(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.linkedin_poster.PENDING_APPROVAL", tmp_path)

        path = create_approval_request("Content here", "#ai #tech", "doc123")
        content = path.read_text()
        assert "type: linkedin_post" in content
        assert "approval_required: true" in content
        assert "status: pending_approval" in content
        assert "platform: linkedin" in content

    def test_file_contains_post_content(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.linkedin_poster.PENDING_APPROVAL", tmp_path)

        path = create_approval_request("We just shipped v2.0!", "#launch")
        content = path.read_text()
        assert "We just shipped v2.0!" in content
        assert "#launch" in content


class TestPostToLinkedin:
    def test_dry_run_returns_true(self, monkeypatch):
        monkeypatch.setattr("src.linkedin_poster.LINKEDIN_DRY_RUN", True)
        assert post_to_linkedin("Test post") is True

    def test_dry_run_does_not_call_api(self, monkeypatch):
        monkeypatch.setattr("src.linkedin_poster.LINKEDIN_DRY_RUN", True)
        with patch("src.linkedin_poster.requests.post") as mock_post:
            post_to_linkedin("Test post")
            mock_post.assert_not_called()

    def test_no_token_returns_false(self, monkeypatch):
        monkeypatch.setattr("src.linkedin_poster.LINKEDIN_DRY_RUN", False)
        monkeypatch.setattr("src.linkedin_poster.LINKEDIN_ACCESS_TOKEN", "")
        assert post_to_linkedin("Test post") is False


class TestProcessApprovedPosts:
    def test_returns_zero_when_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.linkedin_poster.APPROVED", tmp_path)
        assert process_approved_posts() == 0

    def test_processes_approved_post(self, vault, monkeypatch):
        monkeypatch.setattr("src.linkedin_poster.APPROVED", vault["APPROVED"])
        monkeypatch.setattr("src.linkedin_poster.DONE", vault["DONE"])
        monkeypatch.setattr("src.linkedin_poster.LINKEDIN_DRY_RUN", True)

        # Create a fake approved LinkedIn post
        post_file = vault["APPROVED"] / "LINKEDIN_20260217_120000.md"
        post_file.write_text(
            "---\ntype: linkedin_post\nstatus: pending_approval\n---\n\n"
            "## Draft Post\nExciting update from our team!\n\n"
            "## Hashtags\n#business\n",
            encoding="utf-8",
        )

        count = process_approved_posts()
        assert count == 1

        done_files = list(vault["DONE"].glob("LINKEDIN_*.md"))
        assert len(done_files) == 1
