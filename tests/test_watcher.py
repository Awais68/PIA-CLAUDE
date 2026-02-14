"""Tests for src/watcher.py — InboxHandler file processing pipeline."""

import time
from pathlib import Path
from unittest.mock import patch

from src.watcher import InboxHandler, JUNK_PATTERNS


class TestJunkPatterns:
    def test_ds_store_is_junk(self):
        assert ".ds_store" in JUNK_PATTERNS

    def test_thumbs_db_is_junk(self):
        assert "thumbs.db" in JUNK_PATTERNS


class TestSanitiseName:
    def test_alphanumeric_unchanged(self):
        assert InboxHandler._sanitise_name("report2024") == "report2024"

    def test_spaces_replaced(self):
        result = InboxHandler._sanitise_name("my report")
        assert " " not in result
        assert "my_report" == result

    def test_special_chars_replaced(self):
        result = InboxHandler._sanitise_name("file@#$.name")
        assert "@" not in result
        assert "#" not in result

    def test_truncated_to_80(self):
        long_name = "a" * 200
        assert len(InboxHandler._sanitise_name(long_name)) <= 80


class TestWaitForStable:
    def test_returns_true_for_stable_file(self, vault):
        f = vault["INBOX"] / "stable.pdf"
        f.write_bytes(b"some content")
        # Patch the sleep and config to make it fast
        with patch("src.watcher.FILE_STABILITY_WAIT", 0), \
             patch("src.watcher.FILE_STABILITY_CHECKS", 1):
            assert InboxHandler._wait_for_stable(f) is True

    def test_returns_false_for_missing_file(self, vault):
        f = vault["INBOX"] / "gone.pdf"
        with patch("src.watcher.FILE_STABILITY_WAIT", 0):
            assert InboxHandler._wait_for_stable(f) is False

    def test_returns_false_for_empty_file(self, vault):
        f = vault["INBOX"] / "empty.pdf"
        f.write_bytes(b"")  # 0 bytes — size > 0 check never passes
        with patch("src.watcher.FILE_STABILITY_WAIT", 0):
            assert InboxHandler._wait_for_stable(f) is False


class TestWriteMetadata:
    def test_creates_metadata_file(self, vault):
        source = vault["INBOX"] / "test.pdf"
        source.write_bytes(b"content")
        dest = vault["NEEDS_ACTION"] / "FILE_20260214_120000_test.pdf"
        dest.write_bytes(b"content")
        meta = vault["NEEDS_ACTION"] / "FILE_20260214_120000_test.md"

        InboxHandler._write_metadata(meta, source, dest, "hash123")

        assert meta.exists()
        text = meta.read_text()
        assert "original_name: test.pdf" in text
        assert "content_hash: hash123" in text
        assert "status: pending" in text
        assert "size_bytes:" in text


class TestQuarantine:
    def test_moves_file_to_quarantine(self, vault):
        source = vault["INBOX"] / "bad.exe"
        source.write_bytes(b"bad content")

        InboxHandler._quarantine(source, reason="Unsupported file type")

        assert not source.exists()
        quarantined = list(vault["QUARANTINE"].glob("Q_*"))
        assert len(quarantined) >= 1

    def test_writes_reason_file(self, vault):
        source = vault["INBOX"] / "bad2.exe"
        source.write_bytes(b"bad content")

        InboxHandler._quarantine(source, reason="Test reason")

        reason_files = list(vault["QUARANTINE"].glob("*.reason.md"))
        assert len(reason_files) == 1
        text = reason_files[0].read_text()
        assert "Test reason" in text


class TestHandleNewFile:
    def test_ignores_junk_files(self, vault):
        handler = InboxHandler()
        junk = vault["INBOX"] / ".DS_Store"
        junk.write_bytes(b"junk")

        handler._handle_new_file(junk)

        # File should still be in Inbox (not moved anywhere)
        assert junk.exists()
        assert list(vault["NEEDS_ACTION"].glob("FILE_*")) == []

    def test_ignores_tilde_files(self, vault):
        handler = InboxHandler()
        tilde = vault["INBOX"] / "~tempfile.pdf"
        tilde.write_bytes(b"temp")

        handler._handle_new_file(tilde)

        assert tilde.exists()
        assert list(vault["NEEDS_ACTION"].glob("FILE_*")) == []

    def test_quarantines_unsupported_extension(self, vault):
        handler = InboxHandler()
        bad = vault["INBOX"] / "script.exe"
        bad.write_bytes(b"bad content")

        handler._handle_new_file(bad)

        assert not bad.exists()
        assert len(list(vault["QUARANTINE"].glob("Q_*"))) >= 1

    def test_quarantines_oversized_file(self, vault, monkeypatch):
        monkeypatch.setattr("src.watcher.MAX_FILE_SIZE_MB", 0)  # 0 MB limit
        monkeypatch.setattr("src.watcher.FILE_STABILITY_WAIT", 0)
        monkeypatch.setattr("src.watcher.FILE_STABILITY_CHECKS", 1)
        handler = InboxHandler()
        big = vault["INBOX"] / "huge.pdf"
        big.write_bytes(b"x" * 1024)  # any content > 0 MB limit

        handler._handle_new_file(big)

        assert not big.exists()
        assert len(list(vault["QUARANTINE"].glob("Q_*"))) >= 1

    def test_processes_valid_pdf(self, vault, monkeypatch):
        monkeypatch.setattr("src.watcher.FILE_STABILITY_WAIT", 0)
        monkeypatch.setattr("src.watcher.FILE_STABILITY_CHECKS", 1)
        handler = InboxHandler()
        pdf = vault["INBOX"] / "invoice.pdf"
        pdf.write_bytes(b"%PDF-1.4 test content")

        handler._handle_new_file(pdf)

        # File removed from Inbox
        assert not pdf.exists()
        # Metadata + companion in Needs_Action
        mds = list(vault["NEEDS_ACTION"].glob("FILE_*.md"))
        assert len(mds) == 1
        pdfs = list(vault["NEEDS_ACTION"].glob("FILE_*.pdf"))
        assert len(pdfs) == 1

    def test_dedup_skips_second_copy(self, vault, monkeypatch):
        monkeypatch.setattr("src.watcher.FILE_STABILITY_WAIT", 0)
        monkeypatch.setattr("src.watcher.FILE_STABILITY_CHECKS", 1)
        handler = InboxHandler()

        # First copy
        pdf1 = vault["INBOX"] / "doc.pdf"
        pdf1.write_bytes(b"%PDF same content")
        handler._handle_new_file(pdf1)

        # Second copy — same content, different name
        pdf2 = vault["INBOX"] / "doc_copy.pdf"
        pdf2.write_bytes(b"%PDF same content")
        handler._handle_new_file(pdf2)

        # Only one metadata file should exist
        mds = list(vault["NEEDS_ACTION"].glob("FILE_*.md"))
        assert len(mds) == 1

    def test_load_existing_hashes(self, vault, monkeypatch):
        monkeypatch.setattr("src.watcher.FILE_STABILITY_WAIT", 0)
        monkeypatch.setattr("src.watcher.FILE_STABILITY_CHECKS", 1)

        # Pre-populate a metadata file with a known hash
        md = vault["NEEDS_ACTION"] / "FILE_20260214_000000_old.md"
        md.write_text(
            "---\ncontent_hash: deadbeef\nstatus: pending\n---\n",
            encoding="utf-8",
        )

        handler = InboxHandler()
        assert "deadbeef" in handler._seen_hashes
