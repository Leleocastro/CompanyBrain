from ingestao.connectors.gmail.parser import (
    normalize_message,
    normalize_thread,
    _extract_headers,
    _extract_attachments,
    _clean_email,
)


class TestNormalizeMessage:
    def test_basic_message(self, mock_plain_message):
        result = normalize_message(mock_plain_message)
        assert result["id"] == "msg_001"
        assert result["thread_id"] == "thread_001"
        assert result["source"] == "gmail"
        assert result["author"] == "alice@example.com"
        assert result["author_raw"] == "Alice <alice@example.com>"
        assert result["subject"] == "Test"
        assert result["timestamp"] == "1776600000000"
        assert "Hello" in result["text_excerpt"]
        assert result["label_ids"] == ["INBOX"]
        assert result["sha256"] is not None

    def test_message_with_attachments(self, mock_message_with_attachment):
        result = normalize_message(mock_message_with_attachment)
        assert result["id"] == "msg_002"
        assert len(result["attachments"]) == 1
        att = result["attachments"][0]
        assert att["filename"] == "q1_report.pdf"
        assert att["mime_type"] == "application/pdf"
        assert att["attachment_id"] == "att_001"
        assert att["size"] == 54321

    def test_no_sender_falls_back(self):
        msg = {"id": "m1", "snippet": "test"}
        result = normalize_message(msg)
        assert result["author"] == ""
        assert result["sha256"] is not None


class TestNormalizeThread:
    def test_thread_with_messages(self, mock_single_thread):
        result = normalize_thread(mock_single_thread)
        assert result["id"] == "thread_001"
        assert result["source"] == "gmail"
        assert result["message_count"] == 1
        assert len(result["messages"]) == 1
        assert result["sha256"] is not None

    def test_empty_thread(self):
        thread = {"id": "thread_empty", "messages": []}
        result = normalize_thread(thread)
        assert result["message_count"] == 0
        assert result["sha256"] is None


class TestExtractHeaders:
    def test_extract_headers(self, mock_plain_message):
        headers = _extract_headers(mock_plain_message["payload"])
        assert headers["From"] == "Alice <alice@example.com>"
        assert headers["Subject"] == "Test"
        assert headers["Date"] is not None


class TestExtractAttachments:
    def test_no_attachments(self, mock_plain_message):
        atts = _extract_attachments(mock_plain_message["payload"])
        assert atts == []

    def test_with_attachments(self, mock_message_with_attachment):
        atts = _extract_attachments(mock_message_with_attachment["payload"])
        assert len(atts) == 1


class TestCleanEmail:
    def test_clean_email_with_brackets(self):
        assert _clean_email("Alice <alice@example.com>") == "alice@example.com"

    def test_clean_email_plain(self):
        assert _clean_email("alice@example.com") == "alice@example.com"
