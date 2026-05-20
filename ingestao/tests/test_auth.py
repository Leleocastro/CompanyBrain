import os
import pytest
from ingestao.connectors.slack.auth import SlackAuth


def test_auth_from_env(monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test-token")
    auth = SlackAuth.from_env()
    assert auth.token == "xoxb-test-token"


def test_auth_from_env_missing(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    with pytest.raises(ValueError, match="SLACK_BOT_TOKEN is required"):
        SlackAuth.from_env()


def test_auth_with_explicit_token():
    auth = SlackAuth(token="xoxb-my-token")
    assert auth.token == "xoxb-my-token"
