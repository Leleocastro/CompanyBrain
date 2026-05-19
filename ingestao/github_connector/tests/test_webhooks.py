import hashlib
import hmac

from ingestao.github_connector.webhooks import WebhookHandler


class TestWebhookHandler:
    def test_verify_signature_valid(self):
        handler = WebhookHandler("mysecret")
        payload = b'{"test": true}'
        expected = (
            "sha256=" + hmac.new(b"mysecret", payload, hashlib.sha256).hexdigest()
        )
        assert handler.verify_signature(payload, expected)

    def test_verify_signature_invalid(self):
        handler = WebhookHandler("mysecret")
        payload = b'{"test": true}'
        assert not handler.verify_signature(payload, "sha256=invalid")

    def test_process_ping(self):
        handler = WebhookHandler("secret")
        result = handler.process_ping({"hook_id": 123})
        assert result["status"] == "pong"
        assert result["hook_id"] == 123

    def test_process_push(self):
        handler = WebhookHandler("secret")
        data = {
            "ref": "refs/heads/main",
            "repository": {"full_name": "org/repo"},
            "commits": [
                {
                    "id": "abc123",
                    "message": "fix things",
                    "author": {"name": "Alice"},
                    "timestamp": "2026-01-01T00:00:00Z",
                }
            ],
        }
        result = handler.process_push(data)
        assert result["event"] == "push"
        assert result["repo"] == "org/repo"
        assert len(result["commits"]) == 1

    def test_process_pull_request(self):
        handler = WebhookHandler("secret")
        data = {
            "action": "opened",
            "repository": {"full_name": "org/repo"},
            "pull_request": {
                "number": 1,
                "title": "Fix bug",
                "body": "desc",
                "user": {"login": "Bob"},
                "state": "open",
                "html_url": "https://github.com/org/repo/pull/1",
            },
        }
        result = handler.process_pull_request(data)
        assert result["event"] == "pull_request"
        assert result["number"] == 1

    def test_process_issues(self):
        handler = WebhookHandler("secret")
        data = {
            "action": "opened",
            "repository": {"full_name": "org/repo"},
            "issue": {
                "number": 5,
                "title": "Bug report",
                "body": "details",
                "user": {"login": "Charlie"},
                "state": "open",
                "labels": [{"name": "bug"}],
                "html_url": "https://github.com/org/repo/issues/5",
            },
        }
        result = handler.process_issues(data)
        assert result["event"] == "issues"
        assert result["labels"] == ["bug"]
