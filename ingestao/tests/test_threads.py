from ingestao.connectors.slack.threads import fetch_thread, fetch_channel_history


def test_fetch_thread_single_page(mocker):
    client = mocker.Mock()
    client.conversations_replies.return_value = {
        "ok": True,
        "messages": [
            {"ts": "1", "user": "U001", "text": "hello"},
            {"ts": "2", "user": "U002", "text": "world"},
        ],
        "response_metadata": {"next_cursor": ""},
    }
    msgs = fetch_thread(client, "C001", "1.0")
    assert len(msgs) == 2


def test_fetch_channel_history(mocker):
    client = mocker.Mock()
    client.conversations_history.return_value = {
        "ok": True,
        "messages": [{"ts": "1", "user": "U001", "text": "hi"}],
        "response_metadata": {"next_cursor": ""},
    }
    msgs = fetch_channel_history(client, "C001", limit=50)
    assert len(msgs) == 1
    assert msgs[0]["text"] == "hi"
