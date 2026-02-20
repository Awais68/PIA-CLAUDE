"""Tests for src/cross_domain_linker.py — Gold tier G3."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.cross_domain_linker import (
    build_contact_graph,
    extract_email,
    find_related_items,
    get_contact_identity,
    get_contact_path,
    list_contacts,
    load_contact,
    make_contact_key,
    normalize_phone,
    process_item_for_contacts,
    record_interaction,
    save_contact,
)


class TestNormalizePhone:
    def test_strips_non_digits(self):
        assert normalize_phone("+1 (234) 567-8900") == "+12345678900"

    def test_keeps_plus_sign(self):
        assert normalize_phone("+447911123456") == "+447911123456"

    def test_plain_digits(self):
        assert normalize_phone("5551234567") == "5551234567"


class TestExtractEmail:
    def test_plain_email(self):
        assert extract_email("alice@example.com") == "alice@example.com"

    def test_with_display_name(self):
        assert extract_email("Alice Smith <alice@example.com>") == "alice@example.com"

    def test_lowercases(self):
        assert extract_email("Bob@Example.COM") == "bob@example.com"

    def test_returns_none_if_no_email(self):
        assert extract_email("no email here") is None


class TestMakeContactKey:
    def test_email_key(self):
        key = make_contact_key("alice@example.com")
        assert "@" not in key
        assert "." not in key
        assert "alice" in key

    def test_phone_key(self):
        key = make_contact_key("+447911123456")
        assert len(key) > 0

    def test_capped_at_60_chars(self):
        long_identity = "a" * 100 + "@example.com"
        key = make_contact_key(long_identity)
        assert len(key) <= 60


class TestGetContactIdentity:
    def test_gmail_extracts_email(self):
        fm = {"source": "gmail", "sender": "alice@example.com"}
        result = get_contact_identity(fm)
        assert result is not None
        assert result[0] == "alice@example.com"
        assert result[1] == "gmail"

    def test_gmail_with_display_name(self):
        fm = {"source": "gmail", "sender": "Alice <alice@example.com>"}
        result = get_contact_identity(fm)
        assert result[0] == "alice@example.com"

    def test_whatsapp_extracts_phone(self):
        fm = {"source": "whatsapp", "sender": "+1234567890"}
        result = get_contact_identity(fm)
        assert result is not None
        assert result[0] == "+1234567890"
        assert result[1] == "whatsapp"

    def test_file_drop_returns_none(self):
        fm = {"source": "file_drop", "original_name": "report.pdf"}
        result = get_contact_identity(fm)
        assert result is None

    def test_gmail_no_sender_returns_none(self):
        fm = {"source": "gmail", "sender": ""}
        result = get_contact_identity(fm)
        assert result is None


class TestLoadSaveContact:
    def test_load_nonexistent_returns_blank(self, vault):
        contact = load_contact("nobody@example.com")
        assert contact["identity"] == "nobody@example.com"
        assert contact["channels"] == []
        assert contact["interactions"] == []

    def test_save_creates_file(self, vault):
        contact = {
            "identity": "alice@example.com",
            "channels": ["gmail"],
            "interactions": ["[2026-02-18T12:00] [gmail] invoice: inv.pdf"],
            "created_at": "2026-02-18T12:00:00+00:00",
            "display_name": "alice@example.com",
            "last_seen": "2026-02-18T12:00:00+00:00",
        }
        path = save_contact("alice@example.com", contact)
        assert path.exists()
        content = path.read_text()
        assert "alice@example.com" in content
        assert "gmail" in content


class TestRecordInteraction:
    def test_creates_contact_file(self, vault):
        path = record_interaction(
            "alice@example.com", "gmail", "invoice.pdf",
            "invoice", "2026-02-18T12:00:00+00:00"
        )
        assert path.exists()

    def test_adds_channel_on_new_source(self, vault):
        record_interaction(
            "+1234567890", "whatsapp", "msg.txt",
            "text", "2026-02-18T12:00:00+00:00"
        )
        contact = load_contact("+1234567890")
        assert "whatsapp" in contact["channels"]

    def test_interaction_logged(self, vault):
        record_interaction(
            "bob@example.com", "gmail", "report.pdf",
            "other", "2026-02-18T12:00:00+00:00"
        )
        contact = load_contact("bob@example.com")
        assert len(contact["interactions"]) == 1
        assert "report.pdf" in contact["interactions"][0]


class TestProcessItemForContacts:
    def test_gmail_item_creates_contact(self, vault):
        done = vault["DONE"]
        f = done / "FILE_20260218_120000_email.md"
        f.write_text(
            "---\nsource: gmail\nsender: alice@example.com\n"
            "original_name: email.md\ntype: client_email\n"
            "processed_at: 2026-02-18T12:00:00+00:00\n---\n"
        )
        result = process_item_for_contacts(f)
        assert result is not None
        assert result.exists()

    def test_file_drop_returns_none(self, vault):
        done = vault["DONE"]
        f = done / "FILE_20260218_120000_report.md"
        f.write_text(
            "---\nsource: file_drop\noriginal_name: report.pdf\n"
            "type: other\nprocessed_at: 2026-02-18T12:00:00+00:00\n---\n"
        )
        result = process_item_for_contacts(f)
        assert result is None


class TestBuildContactGraph:
    def test_empty_vault(self, vault):
        stats = build_contact_graph()
        assert stats["contacts_updated"] == 0
        assert stats["items_processed"] == 0

    def test_processes_gmail_items(self, vault):
        done = vault["DONE"]
        for i in range(2):
            f = done / f"FILE_20260218_12000{i}_email.md"
            f.write_text(
                f"---\nsource: gmail\nsender: user{i}@example.com\n"
                f"original_name: email{i}.md\ntype: client_email\n"
                f"processed_at: 2026-02-18T12:00:0{i}+00:00\n---\n"
            )
        stats = build_contact_graph(scan_pending=False)
        assert stats["contacts_updated"] == 2


class TestListContacts:
    def test_empty_contacts(self, vault):
        result = list_contacts()
        assert result == []
