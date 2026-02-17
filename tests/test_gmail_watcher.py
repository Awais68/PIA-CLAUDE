"""Tests for src/watchers/gmail_watcher.py — header/body extraction, email file creation."""

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.watchers.gmail_watcher import GmailWatcher


def _make_message(subject="Test Email", from_addr="alice@example.com",
                  body_text="Hello world", has_attachment=False):
    """Build a minimal Gmail API message dict for testing."""
    body_data = base64.urlsafe_b64encode(body_text.encode()).decode()
    parts = [
        {
            "mimeType": "text/plain",
            "body": {"data": body_data},
        }
    ]
    if has_attachment:
        parts.append({
            "mimeType": "application/pdf",
            "filename": "invoice.pdf",
            "body": {"attachmentId": "att_123", "size": 1024},
        })
    return {
        "id": "msg_001",
        "threadId": "thread_001",
        "snippet": body_text[:50],
        "payload": {
            "headers": [
                {"name": "From", "value": from_addr},
                {"name": "To", "value": "me@example.com"},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": "Mon, 17 Feb 2026 12:00:00 +0000"},
            ],
            "parts": parts,
        },
    }


class TestExtractHeaders:
    def test_extracts_common_headers(self):
        msg = _make_message(subject="Invoice #42", from_addr="bob@co.com")
        headers = GmailWatcher._extract_headers(msg)
        assert headers["from"] == "bob@co.com"
        assert headers["subject"] == "Invoice #42"
        assert headers["to"] == "me@example.com"

    def test_missing_headers_returns_empty(self):
        msg = {"payload": {"headers": []}}
        headers = GmailWatcher._extract_headers(msg)
        assert headers == {}

    def test_ignores_non_standard_headers(self):
        msg = {"payload": {"headers": [
            {"name": "X-Custom", "value": "custom_val"},
            {"name": "From", "value": "test@test.com"},
        ]}}
        headers = GmailWatcher._extract_headers(msg)
        assert "x-custom" not in headers
        assert headers["from"] == "test@test.com"


class TestExtractBody:
    def test_extracts_plain_text(self):
        msg = _make_message(body_text="Important meeting tomorrow")
        body = GmailWatcher._extract_body(msg)
        assert "Important meeting tomorrow" in body

    def test_falls_back_to_snippet(self):
        msg = {"snippet": "Snippet text", "payload": {}}
        body = GmailWatcher._extract_body(msg)
        assert body == "Snippet text"

    def test_handles_simple_body(self):
        data = base64.urlsafe_b64encode(b"Simple body").decode()
        msg = {"payload": {"body": {"data": data}}}
        body = GmailWatcher._extract_body(msg)
        assert body == "Simple body"


class TestCreateEmailFile:
    def test_creates_md_file_in_inbox(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.watchers.gmail_watcher.INBOX", tmp_path)
        w = GmailWatcher()
        w.logger = MagicMock()

        headers = {"from": "alice@example.com", "subject": "Test", "to": "me@me.com", "date": "2026-02-17"}
        filepath = w._create_email_file(headers, "Hello body", "msg_001", [])

        assert filepath.exists()
        assert filepath.suffix == ".md"
        content = filepath.read_text()
        assert "source: gmail" in content
        assert "alice@example.com" in content
        assert "Hello body" in content

    def test_includes_attachments_section(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.watchers.gmail_watcher.INBOX", tmp_path)
        w = GmailWatcher()
        w.logger = MagicMock()

        headers = {"from": "a@b.com", "subject": "Inv", "to": "me@me.com", "date": "2026-02-17"}
        filepath = w._create_email_file(headers, "Body", "msg_002", ["/tmp/invoice.pdf"])

        content = filepath.read_text()
        assert "## Attachments" in content
        assert "invoice.pdf" in content

    def test_frontmatter_has_gmail_source(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.watchers.gmail_watcher.INBOX", tmp_path)
        w = GmailWatcher()
        w.logger = MagicMock()

        headers = {"from": "a@b.com", "subject": "S", "to": "me@me.com", "date": "2026-02-17"}
        filepath = w._create_email_file(headers, "Body", "msg_003", [])

        content = filepath.read_text()
        assert "type: email" in content
        assert "source: gmail" in content
        assert "gmail_id: msg_003" in content
        assert "status: pending" in content


class TestGmailWatcherIsBaseWatcher:
    def test_inherits_base_watcher(self):
        from src.watchers.base_watcher import BaseWatcher
        assert issubclass(GmailWatcher, BaseWatcher)

    def test_has_name(self):
        assert GmailWatcher.name == "gmail"

    def test_health_check_works(self):
        w = GmailWatcher()
        h = w.health()
        assert h["watcher"] == "gmail"
        assert h["running"] is False
