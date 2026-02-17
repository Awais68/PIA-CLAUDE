"""Tests for src/mcp/email_server.py — email MCP tools."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.mcp.email_server import send_email, search_emails, list_recent_emails


class TestSendEmail:
    def test_creates_approval_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.mcp.email_server.PENDING_APPROVAL", tmp_path)

        result = send_email("alice@example.com", "Test Subject", "Hello body")

        assert "approval" in result.lower()
        files = list(tmp_path.glob("SEND_EMAIL_*.md"))
        assert len(files) == 1

    def test_file_contains_email_details(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.mcp.email_server.PENDING_APPROVAL", tmp_path)

        send_email("bob@co.com", "Invoice #42", "Please pay $500")

        files = list(tmp_path.glob("SEND_EMAIL_*.md"))
        content = files[0].read_text()
        assert "bob@co.com" in content
        assert "Invoice #42" in content
        assert "Please pay $500" in content

    def test_does_not_actually_send(self, tmp_path, monkeypatch):
        """send_email should ONLY create a file, never call Gmail API."""
        monkeypatch.setattr("src.mcp.email_server.PENDING_APPROVAL", tmp_path)

        with patch("src.mcp.email_server._get_gmail_service") as mock_svc:
            send_email("test@test.com", "Test", "Body")
            mock_svc.assert_not_called()

    def test_frontmatter_has_approval_required(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.mcp.email_server.PENDING_APPROVAL", tmp_path)

        send_email("x@y.com", "S", "B")

        files = list(tmp_path.glob("SEND_EMAIL_*.md"))
        content = files[0].read_text()
        assert "approval_required: true" in content
        assert "status: pending_approval" in content
        assert "type: email_send" in content


class TestSearchEmails:
    def test_returns_formatted_results(self, monkeypatch):
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg_1"}, {"id": "msg_2"}]
        }
        mock_service.users().messages().get().execute.return_value = {
            "payload": {
                "headers": [
                    {"name": "From", "value": "alice@co.com"},
                    {"name": "Subject", "value": "Project Update"},
                    {"name": "Date", "value": "Mon, 17 Feb 2026"},
                ]
            }
        }
        monkeypatch.setattr("src.mcp.email_server._get_gmail_service", lambda: mock_service)

        result = search_emails("from:alice")
        assert "Found 2 email(s)" in result
        assert "Project Update" in result

    def test_returns_empty_message(self, monkeypatch):
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {"messages": []}
        monkeypatch.setattr("src.mcp.email_server._get_gmail_service", lambda: mock_service)

        result = search_emails("nonexistent_query")
        assert "No emails found" in result


class TestListRecentEmails:
    def test_delegates_to_search(self, monkeypatch):
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {"messages": []}
        monkeypatch.setattr("src.mcp.email_server._get_gmail_service", lambda: mock_service)

        result = list_recent_emails(5)
        assert "No emails found" in result
