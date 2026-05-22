from ingestao.connectors.gmail.client import GmailClient


class TestGmailClient:
    def test_default_mock_mode(self):
        client = GmailClient()
        assert client._is_mock is True

    def test_real_token_not_mock(self):
        client = GmailClient(access_token="ya29.real_token")
        assert client._is_mock is False

    def test_list_threads_mock(self):
        client = GmailClient()
        result = client.list_threads(max_results=3)
        threads = result["threads"]
        assert len(threads) == 3
        assert threads[0]["id"] == "thread_001"

    def test_list_threads_max_results(self):
        client = GmailClient()
        result = client.list_threads(max_results=1)
        assert len(result["threads"]) == 1

    def test_get_thread_mock(self):
        client = GmailClient()
        thread = client.get_thread("thread_001")
        assert thread["id"] == "thread_001"
        assert len(thread["messages"]) > 0
        assert thread["messages"][0]["id"] == "thread_001_msg_1"

    def test_get_message_mock(self):
        client = GmailClient()
        msg = client.get_message("msg_001")
        assert msg["id"] == "msg_001"
        assert msg["payload"]["mimeType"] == "multipart/mixed"

    def test_list_messages_mock(self):
        client = GmailClient()
        result = client.list_messages(query="from:alice", max_results=2)
        assert len(result["messages"]) == 2
        assert result["messages"][0]["id"] == "msg_001"

    def test_download_attachment_mock(self):
        client = GmailClient()
        data = client.download_attachment("msg_001", "att_001")
        assert data == b"mock attachment content"
