import pytest
from ingestao.connectors.gmail import auth, client, parser, config


def test_modules_importable():
    # basic smoke test: modules load and expose expected callables/classes
    assert hasattr(auth, "GmailAuth")
    assert hasattr(client, "GmailClient")
    assert hasattr(parser, "normalize_message")
    cfg = config.get_config()
    assert isinstance(cfg, dict)


def test_normalize_message_minimal():
    sample = {"id": "m1", "snippet": "hello world", "from": "user@example.com", "internalDate": 123}
    norm = parser.normalize_message(sample)
    assert norm["id"] == "m1"
    assert norm["author"] == "user@example.com"
    assert "text_excerpt" in norm
