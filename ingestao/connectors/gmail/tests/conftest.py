import pytest


@pytest.fixture
def mock_threads_list():
    return {
        "threads": [
            {"id": "thread_001", "snippet": "Meeting tomorrow", "historyId": "12345"},
            {"id": "thread_002", "snippet": "Invoice attached", "historyId": "12346"},
        ],
        "resultSizeEstimate": 2,
    }


@pytest.fixture
def mock_single_thread():
    return {
        "id": "thread_001",
        "historyId": "12345",
        "messages": [
            {
                "id": "msg_001",
                "threadId": "thread_001",
                "labelIds": ["INBOX", "IMPORTANT"],
                "snippet": "This is the first message",
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


@pytest.fixture
def mock_plain_message():
    return {
        "id": "msg_001",
        "threadId": "thread_001",
        "labelIds": ["INBOX"],
        "snippet": "Hello World",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "Alice <alice@example.com>"},
                {"name": "To", "value": "Bob <bob@example.com>"},
                {"name": "Subject", "value": "Test"},
                {"name": "Date", "value": "Mon, 19 May 2026 10:00:00 +0000"},
            ],
            "body": {"data": "SGVsbG8gV29ybGQ="},
        },
        "internalDate": "1776600000000",
    }


@pytest.fixture
def mock_message_with_attachment():
    return {
        "id": "msg_002",
        "threadId": "thread_001",
        "labelIds": ["INBOX", "IMPORTANT"],
        "snippet": "Please find the report attached",
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "From", "value": "Charlie <charlie@example.com>"},
                {"name": "To", "value": "Dave <dave@example.com>"},
                {"name": "Subject", "value": "Report Q1"},
                {"name": "Date", "value": "Tue, 20 May 2026 14:30:00 +0000"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": "UGxlYXNlIHNlZSB0aGUgYXR0YWNoZWQgcmVwb3J0"},
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "q1_report.pdf",
                    "body": {
                        "attachmentId": "att_001",
                        "size": 54321,
                    },
                },
            ],
        },
        "internalDate": "1776681000000",
    }
