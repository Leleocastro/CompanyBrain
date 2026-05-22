from ingestao.connectors.slack.normalize import normalize_message


def test_normalize_basic_message():
    raw = {
        "ts": "1234567890.000001",
        "user": "U001",
        "text": "Hello world",
    }
    doc = normalize_message(raw, "C001")
    assert doc.id == "slack:C001:1234567890.000001"
    assert doc.author == "U001"
    assert doc.source == "slack"
    assert doc.channel == "C001"
    assert doc.text_excerpt == "Hello world"
    assert doc.thread_ts is None
    assert len(doc.sha256) == 64


def test_normalize_message_with_thread():
    raw = {
        "ts": "1234567891.000002",
        "user": "U002",
        "text": "A reply",
        "thread_ts": "1234567890.000001",
    }
    doc = normalize_message(raw, "C001")
    assert doc.thread_ts == "1234567890.000001"
    assert doc.metadata["has_thread"] is True


def test_normalize_message_with_files():
    raw = {
        "ts": "1234567892.000003",
        "user": "U003",
        "text": "Here is a file",
        "files": [{"id": "F001", "name": "doc.pdf", "size": 1024}],
    }
    doc = normalize_message(raw, "C001")
    assert len(doc.attachments) == 1
    assert doc.attachments[0]["id"] == "F001"


def test_normalize_empty_text():
    raw = {"ts": "0", "user": "U001"}
    doc = normalize_message(raw, "C001")
    assert doc.text_excerpt == ""
    assert doc.author == "U001"
