#!/usr/bin/env python3
"""Smoke test for the Gmail connector — runs entirely with mock fixtures.

No real credentials or network access required. Verifies that all modules
load, the OAuth flow returns expected mock values, the client returns fixture
data, and the parser produces canonical output.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ingestao.connectors.gmail.auth import GmailAuth
from ingestao.connectors.gmail.client import GmailClient
from ingestao.connectors.gmail.config import GmailConfig, get_config
from ingestao.connectors.gmail.parser import normalize_message, normalize_thread


def test_imports():
    assert GmailAuth is not None
    assert GmailClient is not None
    assert GmailConfig is not None
    print("[PASS] All modules importable")


def test_config():
    cfg = get_config()
    assert isinstance(cfg, dict)
    assert "GMAIL_CLIENT_ID" in cfg
    assert "GMAIL_MAX_RESULTS" in cfg
    print("[PASS] Config returns dict with all keys")

    dc = GmailConfig.from_env()
    assert dc.max_results == 20
    print("[PASS] GmailConfig.from_env() works")


def test_auth_mock_flow():
    auth = GmailAuth()
    assert auth._is_mock

    url = auth.get_authorize_url(state="test123")
    assert "accounts.google.com" in url
    assert "state=test123" in url
    assert "offline" in url
    print(f"[PASS] Authorize URL generated: {url[:60]}...")

    tokens = auth.exchange_code("dummy_code")
    assert tokens["access_token"] == "mock_access_token"
    assert tokens["refresh_token"] == "mock_refresh_token"
    print("[PASS] Token exchange returns mock tokens")

    refreshed = auth.refresh_token("dummy_refresh")
    assert refreshed["access_token"] == "mock_refreshed_token"
    print("[PASS] Token refresh works in mock mode")


def test_client_mock_flow():
    client = GmailClient()
    assert client._is_mock

    threads = client.list_threads(max_results=3)
    assert len(threads["threads"]) == 3
    assert threads["threads"][0]["id"] == "thread_001"
    print("[PASS] list_threads() returns 3 fixture threads")

    thread = client.get_thread("thread_001")
    assert thread["id"] == "thread_001"
    print(
        f"[PASS] get_thread() returns thread with {len(thread['messages'])} message(s)"
    )

    msg = client.get_message("msg_002")
    assert msg["id"] == "msg_002"
    print("[PASS] get_message() returns message fixture")

    results = client.list_messages(query="from:test", max_results=5)
    assert len(results["messages"]) >= 2
    print("[PASS] list_messages() returns fixture messages")

    data = client.download_attachment("msg_001", "att_001")
    assert data == b"mock attachment content"
    print("[PASS] download_attachment() returns bytes")


def test_parser():
    msg = {
        "id": "m1",
        "threadId": "t1",
        "labelIds": ["INBOX"],
        "snippet": "Hello smoke test",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "Alice <alice@example.com>"},
                {"name": "To", "value": "Bob <bob@example.com>"},
                {"name": "Subject", "value": "Smoke Test"},
                {"name": "Date", "value": "Mon, 19 May 2026 10:00:00 +0000"},
            ],
            "body": {"data": "U21va2UgdGVzdCBib2R5"},
        },
        "internalDate": "1776600000000",
    }
    result = normalize_message(msg)
    assert result["id"] == "m1"
    assert result["author"] == "alice@example.com"
    assert result["subject"] == "Smoke Test"
    assert result["source"] == "gmail"
    assert len(result["text_excerpt"]) > 0
    assert result["sha256"] is not None
    print(
        f"[PASS] normalize_message() -> author={result['author']}, sha256={result['sha256'][:16]}..."
    )

    thread = {
        "id": "t1",
        "messages": [msg],
    }
    t_result = normalize_thread(thread)
    assert t_result["message_count"] == 1
    assert t_result["sha256"] is not None
    print(f"[PASS] normalize_thread() -> {t_result['message_count']} message(s)")


if __name__ == "__main__":
    print("=" * 50)
    print("Gmail Connector — Local Smoke Test (mock fixtures)")
    print("=" * 50)
    failures = 0
    tests = [
        test_imports,
        test_config,
        test_auth_mock_flow,
        test_client_mock_flow,
        test_parser,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
            import traceback

            traceback.print_exc()
            failures += 1
    print("=" * 50)
    if failures:
        print(f"RESULT: {failures} test(s) FAILED")
        sys.exit(1)
    else:
        print(f"RESULT: All {len(tests)} smoke tests PASSED")
        sys.exit(0)
