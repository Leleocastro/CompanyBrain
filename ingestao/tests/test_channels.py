from ingestao.connectors.slack.channels import list_channels


def test_list_channels_single_page(mocker):
    client = mocker.Mock()
    client.conversations_list.return_value = {
        "ok": True,
        "channels": [
            {"id": "C001", "name": "general", "num_members": 42},
            {"id": "C002", "name": "random", "num_members": 15},
        ],
        "response_metadata": {"next_cursor": ""},
    }
    result = list_channels(client, limit=200)
    assert len(result) == 2
    assert result[0]["name"] == "general"


def test_list_channels_pagination(mocker):
    client = mocker.Mock()
    client.conversations_list.side_effect = [
        {
            "ok": True,
            "channels": [{"id": "C001", "name": "general"}],
            "response_metadata": {"next_cursor": "abc"},
        },
        {
            "ok": True,
            "channels": [{"id": "C002", "name": "random"}],
            "response_metadata": {"next_cursor": ""},
        },
    ]
    result = list_channels(client, limit=200)
    assert len(result) == 2
    assert client.conversations_list.call_count == 2


def test_list_channels_respects_limit(mocker):
    client = mocker.Mock()
    client.conversations_list.return_value = {
        "ok": True,
        "channels": [{"id": "C001", "name": "general"}],
        "response_metadata": {"next_cursor": ""},
    }
    result = list_channels(client, limit=1)
    assert len(result) == 1
