import pytest
from unittest.mock import MagicMock
from slack_sdk.errors import SlackApiError
from ingestao.connectors.slack.client import SlackClient


def test_client_rate_limit_retry(mocker, monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    client = SlackClient()
    import time
    time_mock = mocker.patch("time.sleep")

    resp_ok = mocker.MagicMock()
    resp_ok.data = {"ok": True, "channels": []}
    resp_ok.__getitem__.side_effect = lambda k: {"ok": True, "channels": []}[k]
    resp_ok.get = lambda k, d=None: {"ok": True, "channels": []}.get(k, d)
    resp_ok.headers = {}

    resp_rate = mocker.MagicMock()
    resp_rate.data = {"ok": False, "error": "ratelimited"}
    resp_rate.__getitem__.side_effect = lambda k: {"ok": False, "error": "ratelimited"}[k]
    resp_rate.get = lambda k, d=None: {"ok": False, "error": "ratelimited"}.get(k, d)
    resp_rate.headers = {"Retry-After": "1"}

    # Make sure the SlackApiError's `.response` attribute returns the mock
    resp_rate.configure_mock(response=resp_rate)

    client._client.conversations_list = mocker.Mock(
        side_effect=[SlackApiError("rate", resp_rate), resp_ok]
    )

    result = client.conversations_list()
    assert result["ok"] is True
    assert time_mock.called


def test_client_non_retryable_error(mocker, monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    client = SlackClient()

    resp_err = mocker.MagicMock()
    resp_err.__getitem__.side_effect = lambda k: "invalid_auth" if k == "error" else None
    resp_err.data = {"ok": False, "error": "invalid_auth"}

    client._client.conversations_list = mocker.Mock(
        side_effect=SlackApiError("auth", resp_err)
    )

    with pytest.raises(SlackApiError):
        client.conversations_list()
