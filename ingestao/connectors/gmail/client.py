import base64
import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, List, Optional


GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailClient:
    def __init__(self, access_token: Optional[str] = None, credentials: Optional[Dict] = None):
        self.access_token = access_token
        self.credentials = credentials or {}

    @property
    def _is_mock(self) -> bool:
        return self.access_token is None or self.access_token.startswith("mock_")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token or 'mock_token'}",
            "Content-Type": "application/json",
        }

    def list_threads(self, max_results: int = 20, page_token: Optional[str] = None) -> Dict:
        if self._is_mock:
            return _mock_list_threads(max_results)
        params: Dict[str, object] = {"maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token
        url = f"{GMAIL_API_BASE}/threads?{urllib.parse.urlencode(params)}"
        return self._get(url)

    def get_thread(self, thread_id: str, format: str = "full") -> Dict:
        if self._is_mock:
            return _mock_get_thread(thread_id)
        url = f"{GMAIL_API_BASE}/threads/{urllib.parse.quote(thread_id)}?format={format}"
        return self._get(url)

    def get_message(self, message_id: str, format: str = "full") -> Dict:
        if self._is_mock:
            return _mock_get_message(message_id)
        url = f"{GMAIL_API_BASE}/messages/{urllib.parse.quote(message_id)}?format={format}"
        return self._get(url)

    def list_messages(
        self, query: str = "", max_results: int = 20, page_token: Optional[str] = None
    ) -> Dict:
        if self._is_mock:
            return _mock_list_messages(query, max_results)
        params: Dict[str, object] = {"maxResults": max_results}
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token
        url = f"{GMAIL_API_BASE}/messages?{urllib.parse.urlencode(params)}"
        return self._get(url)

    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        if self._is_mock:
            return b"mock attachment content"
        url = (
            f"{GMAIL_API_BASE}/messages/{urllib.parse.quote(message_id)}"
            f"/attachments/{urllib.parse.quote(attachment_id)}"
        )
        data = self._get(url)
        return base64.urlsafe_b64decode(data.get("data", ""))

    def _get(self, url: str) -> Dict:
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(f"Gmail API error {e.code}: {error_body}") from e


MOCK_FIXTURES = {
    "threads": [
        {"id": "thread_001", "snippet": "Meeting tomorrow at 10am", "historyId": "12345"},
        {"id": "thread_002", "snippet": "Invoice attached for January", "historyId": "12346"},
        {"id": "thread_003", "snippet": "Re: Project update - Q1 results", "historyId": "12347"},
        {"id": "thread_004", "snippet": "Welcome to CompanyBrain!", "historyId": "12348"},
        {"id": "thread_005", "snippet": "Your subscription is expiring", "historyId": "12349"},
    ],
}


def _mock_list_threads(max_results: int = 20) -> Dict:
    threads = MOCK_FIXTURES["threads"][:max_results]
    return {"threads": threads, "resultSizeEstimate": len(threads)}


def _mock_get_thread(thread_id: str) -> Dict:
    return {
        "id": thread_id,
        "historyId": "12345",
        "messages": [
            {
                "id": f"{thread_id}_msg_1",
                "threadId": thread_id,
                "labelIds": ["INBOX", "IMPORTANT"],
                "snippet": "This is the first message in the thread",
                "payload": {
                    "mimeType": "text/plain",
                    "headers": [
                        {"name": "From", "value": "Alice <alice@example.com>"},
                        {"name": "To", "value": "Bob <bob@example.com>"},
                        {"name": "Subject", "value": "Test Thread"},
                        {"name": "Date", "value": "Mon, 19 May 2026 10:00:00 +0000"},
                    ],
                },
                "internalDate": "1776600000000",
            }
        ],
    }


def _mock_get_message(message_id: str) -> Dict:
    return {
        "id": message_id,
        "threadId": "thread_001",
        "labelIds": ["INBOX"],
        "snippet": "This is a mocked email message",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "From", "value": "Alice <alice@example.com>"},
                {"name": "To", "value": "Bob <bob@example.com>"},
                {"name": "Subject", "value": "Mock Message"},
                {"name": "Date", "value": "Mon, 19 May 2026 10:00:00 +0000"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": "SGVsbG8gV29ybGQ="},
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "report.pdf",
                    "body": {
                        "attachmentId": "att_001",
                        "size": 12345,
                    },
                },
            ],
        },
        "internalDate": "1776600000000",
    }


def _mock_list_messages(query: str = "", max_results: int = 20) -> Dict:
    messages = [
        {"id": "msg_001", "threadId": "thread_001"},
        {"id": "msg_002", "threadId": "thread_002"},
        {"id": "msg_003", "threadId": "thread_003"},
    ][:max_results]
    return {"messages": messages, "resultSizeEstimate": len(messages)}
