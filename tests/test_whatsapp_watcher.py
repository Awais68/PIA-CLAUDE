"""Tests for src/watchers/whatsapp_watcher.py — WhatsApp webhook watcher."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.watchers.whatsapp_watcher import WhatsAppWatcher


def _make_webhook_payload(from_number="1234567890", body="Hello from WhatsApp", msg_type="text"):
    """Build a minimal Meta Cloud API webhook payload for testing."""
    message = {
        "from": from_number,
        "id": "wamid_test_001",
        "timestamp": "1708185600",
        "type": msg_type,
    }
    if msg_type == "text":
        message["text"] = {"body": body}
    elif msg_type == "image":
        message["image"] = {"id": "media_123", "caption": body or "Photo"}
    elif msg_type == "document":
        message["document"] = {"id": "media_456", "filename": body or "file.pdf"}

    return {
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "messages": [message],
                },
                "field": "messages",
            }],
        }],
    }


class TestExtractMessages:
    def test_extracts_text_message(self):
        payload = _make_webhook_payload(body="Test message")
        messages = WhatsAppWatcher._extract_messages(payload)
        assert len(messages) == 1
        assert messages[0]["body"] == "Test message"
        assert messages[0]["from"] == "1234567890"
        assert messages[0]["type"] == "text"

    def test_extracts_image_message(self):
        payload = _make_webhook_payload(body="Nice photo", msg_type="image")
        messages = WhatsAppWatcher._extract_messages(payload)
        assert len(messages) == 1
        assert messages[0]["type"] == "image"
        assert messages[0]["media_id"] == "media_123"

    def test_extracts_document_message(self):
        payload = _make_webhook_payload(body="invoice.pdf", msg_type="document")
        messages = WhatsAppWatcher._extract_messages(payload)
        assert len(messages) == 1
        assert messages[0]["type"] == "document"
        assert messages[0]["media_id"] == "media_456"

    def test_empty_payload_returns_empty(self):
        messages = WhatsAppWatcher._extract_messages({})
        assert messages == []

    def test_no_messages_returns_empty(self):
        payload = {"entry": [{"changes": [{"value": {}}]}]}
        messages = WhatsAppWatcher._extract_messages(payload)
        assert messages == []


class TestProcessMessage:
    def test_creates_md_file_in_inbox(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.watchers.whatsapp_watcher.INBOX", tmp_path)
        w = WhatsAppWatcher()
        w.logger = MagicMock()

        msg = {"from": "+15551234567", "body": "Order #42 status?", "type": "text"}
        filepath = w._process_message(msg)

        assert filepath.exists()
        assert filepath.suffix == ".md"
        content = filepath.read_text()
        assert "source: whatsapp" in content
        assert "Order #42 status?" in content
        assert "+15551234567" in content

    def test_frontmatter_has_whatsapp_source(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.watchers.whatsapp_watcher.INBOX", tmp_path)
        w = WhatsAppWatcher()
        w.logger = MagicMock()

        msg = {"from": "+1000", "body": "Hi", "type": "text"}
        filepath = w._process_message(msg)

        content = filepath.read_text()
        assert "type: whatsapp_message" in content
        assert "source: whatsapp" in content
        assert "status: pending" in content

    def test_filename_contains_whatsapp_prefix(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.watchers.whatsapp_watcher.INBOX", tmp_path)
        w = WhatsAppWatcher()
        w.logger = MagicMock()

        msg = {"from": "+1000", "body": "Test", "type": "text"}
        filepath = w._process_message(msg)
        assert filepath.name.startswith("WHATSAPP_")


class TestWhatsAppWatcherIsBaseWatcher:
    def test_inherits_base_watcher(self):
        from src.watchers.base_watcher import BaseWatcher
        assert issubclass(WhatsAppWatcher, BaseWatcher)

    def test_has_name(self):
        assert WhatsAppWatcher.name == "whatsapp"

    def test_health_check(self):
        w = WhatsAppWatcher()
        h = w.health()
        assert h["watcher"] == "whatsapp"
        assert h["running"] is False


class TestWebhookVerification:
    def test_verify_endpoint(self):
        w = WhatsAppWatcher()
        client = w._app.test_client()
        resp = client.get("/webhook?hub.mode=subscribe&hub.verify_token=zoya_verify_token&hub.challenge=test123")
        assert resp.status_code == 200
        assert resp.data == b"test123"

    def test_verify_rejects_bad_token(self):
        w = WhatsAppWatcher()
        client = w._app.test_client()
        resp = client.get("/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=test123")
        assert resp.status_code == 403

    def test_webhook_post_queues_message(self):
        w = WhatsAppWatcher()
        client = w._app.test_client()
        payload = _make_webhook_payload(body="Incoming message")
        resp = client.post("/webhook", json=payload)
        assert resp.status_code == 200
        assert len(w._message_queue) == 1

    def test_test_message_endpoint(self):
        w = WhatsAppWatcher()
        client = w._app.test_client()
        resp = client.post("/test-message", json={"body": "Test msg", "from": "+999"})
        assert resp.status_code == 200
        assert len(w._message_queue) == 1

    def test_health_endpoint(self):
        w = WhatsAppWatcher()
        client = w._app.test_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["watcher"] == "whatsapp"


class TestPollCycle:
    def test_poll_processes_queued_messages(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.watchers.whatsapp_watcher.INBOX", tmp_path)
        w = WhatsAppWatcher()
        w.logger = MagicMock()
        w._message_queue = [
            {"from": "+1111", "body": "Msg 1", "type": "text"},
            {"from": "+2222", "body": "Msg 2", "type": "text"},
        ]
        count = w.poll()
        assert count == 2
        assert len(list(tmp_path.glob("WHATSAPP_*.md"))) == 2

    def test_poll_returns_zero_when_empty(self):
        w = WhatsAppWatcher()
        assert w.poll() == 0
