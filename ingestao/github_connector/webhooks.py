from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self, secret: str) -> None:
        self.secret = secret.encode("utf-8")
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event: str) -> Callable:
        def decorator(fn: Callable) -> Callable:
            self._handlers.setdefault(event, []).append(fn)
            return fn

        return decorator

    def verify_signature(self, payload: bytes, signature_header: str) -> bool:
        expected = (
            "sha256=" + hmac.new(self.secret, payload, hashlib.sha256).hexdigest()
        )
        return hmac.compare_digest(expected, signature_header)

    async def handle(self, payload: bytes, headers: dict[str, str]) -> list[Any]:
        sig = headers.get("X-Hub-Signature-256", "")
        if not self.verify_signature(payload, sig):
            raise ValueError("Invalid webhook signature")

        event = headers.get("X-GitHub-Event", "unknown")
        data = json.loads(payload)

        results: list[Any] = []
        handlers = self._handlers.get(event, [])
        for handler in handlers:
            try:
                result = await handler(data)
                results.append(result)
            except Exception as e:
                logger.error("Webhook handler %s failed: %s", handler.__name__, e)
        return results

    def process_ping(self, data: dict) -> dict:
        return {"status": "pong", "hook_id": data.get("hook_id")}

    def process_push(self, data: dict) -> Optional[dict]:
        ref = data.get("ref", "")
        repo = data.get("repository", {})
        return {
            "event": "push",
            "ref": ref,
            "repo": repo.get("full_name"),
            "commits": [
                {
                    "sha": c["id"],
                    "message": c.get("message", ""),
                    "author": c.get("author", {}).get("name"),
                    "timestamp": c.get("timestamp"),
                }
                for c in data.get("commits", [])
            ],
        }

    def process_pull_request(self, data: dict) -> Optional[dict]:
        pr = data.get("pull_request", {})
        repo = data.get("repository", {})
        return {
            "event": "pull_request",
            "action": data.get("action"),
            "repo": repo.get("full_name"),
            "number": pr.get("number"),
            "title": pr.get("title"),
            "body": pr.get("body"),
            "author": pr.get("user", {}).get("login"),
            "state": pr.get("state"),
            "url": pr.get("html_url"),
        }

    def process_issues(self, data: dict) -> Optional[dict]:
        issue = data.get("issue", {})
        repo = data.get("repository", {})
        return {
            "event": "issues",
            "action": data.get("action"),
            "repo": repo.get("full_name"),
            "number": issue.get("number"),
            "title": issue.get("title"),
            "body": issue.get("body"),
            "author": issue.get("user", {}).get("login"),
            "state": issue.get("state"),
            "labels": [lb["name"] for lb in issue.get("labels", [])],
            "url": issue.get("html_url"),
        }
