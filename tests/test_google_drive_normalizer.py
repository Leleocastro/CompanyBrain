"""Tests for the Google Drive normalizer and PII redaction."""

from datetime import datetime

from ingestao.connectors.base import Document
from ingestao.connectors.google_drive.models import DriveFile
from ingestao.connectors.google_drive.normalizer import drive_file_to_document
from ingestao.pii import redact_pii, has_pii
from ingestao.normalizer import compute_sha256, safe_timestamp


class TestNormalizer:
    def test_drive_file_to_document_basic(self):
        df = DriveFile(
            id="f1",
            name="doc.txt",
            mime_type="text/plain",
            size=100,
            owners=["Alice"],
            last_modifying_user="Bob",
        )
        doc = drive_file_to_document(df, raw_bytes=b"hello world", text_content="hello world")
        assert isinstance(doc, Document)
        assert doc.id == "f1"
        assert doc.title == "doc.txt"
        assert doc.author == "Bob"
        assert doc.sha256 == compute_sha256(b"hello world")
        assert doc.text_content == "hello world"

    def test_drive_file_to_document_no_raw_bytes(self):
        df = DriveFile(id="f2", name="note.txt", mime_type="text/plain")
        doc = drive_file_to_document(df)
        assert doc.sha256 is None
        assert doc.raw_bytes is None

    def test_drive_file_to_document_with_timestamp(self):
        ts = datetime(2025, 6, 1, 12, 0, 0)
        df = DriveFile(
            id="f3", name="a.txt", mime_type="text/plain",
            modified_time=ts,
        )
        doc = drive_file_to_document(df)
        assert doc.timestamp == ts


class TestPIIRedaction:
    def test_redact_email(self):
        text = "Contact me at john.doe@example.com or support@company.org"
        result = redact_pii(text)
        assert "[EMAIL]" in result
        assert "john.doe@example.com" not in result

    def test_redact_phone(self):
        text = "Call 555-123-4567 or 555.987.6543"
        result = redact_pii(text)
        assert "[PHONE]" in result
        assert "555-123-4567" not in result

    def test_redact_ssn(self):
        text = "SSN: 123-45-6789"
        result = redact_pii(text)
        assert "[SSN]" in result
        assert "123-45-6789" not in result

    def test_has_pii_true(self):
        assert has_pii("email: user@test.com") is True

    def test_has_pii_false(self):
        assert has_pii("just plain text") is False

    def test_normalizer_applies_redaction(self):
        df = DriveFile(id="pii1", name="contacts.txt", mime_type="text/plain")
        doc = drive_file_to_document(
            df, raw_bytes=b"Email: alice@example.com",
            text_content="Email: alice@example.com",
        )
        assert "alice@example.com" not in (doc.text_content or "")
        assert "[EMAIL]" in (doc.text_content or "")


class TestSha256:
    def test_compute_sha256(self):
        h = compute_sha256(b"hello")
        assert isinstance(h, str)
        assert len(h) == 64


class TestSafeTimestamp:
    def test_valid_rfc3339(self):
        dt = safe_timestamp("2025-01-15T10:30:00.000Z")
        assert dt is not None
        assert dt.year == 2025

    def test_valid_iso(self):
        dt = safe_timestamp("2025-01-15T10:30:00Z")
        assert dt is not None

    def test_invalid(self):
        assert safe_timestamp("not-a-date") is None

    def test_none(self):
        assert safe_timestamp(None) is None
