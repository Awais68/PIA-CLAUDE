"""Tests for cross-domain integration — source normalizer and priority handling."""

from src.source_normalizer import (
    get_source_priority,
    normalize_metadata,
    sort_by_priority,
)


class TestNormalizeMetadata:
    def test_file_drop(self):
        raw = {"original_name": "report.pdf", "status": "pending", "type": "file_drop"}
        result = normalize_metadata("file_drop", raw)
        assert result["source"] == "file_drop"
        assert result["original_name"] == "report.pdf"
        assert result["status"] == "pending"

    def test_gmail(self):
        raw = {"from": "alice@co.com", "subject": "Invoice", "status": "pending", "gmail_id": "msg_001"}
        result = normalize_metadata("gmail", raw)
        assert result["source"] == "gmail"
        assert result["sender"] == "alice@co.com"
        assert result["subject"] == "Invoice"
        assert result["gmail_id"] == "msg_001"

    def test_whatsapp(self):
        raw = {"from": "+1234567890", "message_type": "text", "status": "pending"}
        result = normalize_metadata("whatsapp", raw)
        assert result["source"] == "whatsapp"
        assert result["sender"] == "+1234567890"
        assert result["message_type"] == "text"

    def test_defaults_for_missing_fields(self):
        result = normalize_metadata("file_drop", {})
        assert result["status"] == "pending"
        assert result["priority"] == "low"
        assert result["type"] == "other"


class TestSourcePriority:
    def test_whatsapp_highest(self):
        assert get_source_priority("whatsapp") > get_source_priority("gmail")
        assert get_source_priority("whatsapp") > get_source_priority("file_drop")

    def test_gmail_higher_than_file(self):
        assert get_source_priority("gmail") > get_source_priority("file_drop")

    def test_unknown_source_zero(self):
        assert get_source_priority("unknown") == 0


class TestSortByPriority:
    def test_whatsapp_comes_first(self):
        items = [
            {"source": "file_drop", "received_at": "2026-02-17T10:00:00"},
            {"source": "whatsapp", "received_at": "2026-02-17T10:01:00"},
            {"source": "gmail", "received_at": "2026-02-17T10:02:00"},
        ]
        sorted_items = sort_by_priority(items)
        assert sorted_items[0]["source"] == "whatsapp"
        assert sorted_items[1]["source"] == "gmail"
        assert sorted_items[2]["source"] == "file_drop"

    def test_same_source_sorted_by_time(self):
        items = [
            {"source": "gmail", "received_at": "2026-02-17T10:05:00"},
            {"source": "gmail", "received_at": "2026-02-17T10:00:00"},
        ]
        sorted_items = sort_by_priority(items)
        assert sorted_items[0]["received_at"] == "2026-02-17T10:00:00"

    def test_empty_list(self):
        assert sort_by_priority([]) == []
