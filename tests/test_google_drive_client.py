"""Tests for the Google Drive connector."""

import os

from ingestao.connectors.google_drive.client import GoogleDriveConnector


class TestConnectorInstantiation:
    def test_connector_class_exists(self):
        c = GoogleDriveConnector()
        assert c is not None
        assert not c.is_authenticated()

    def test_authenticate_without_creds_returns_false(self):
        c = GoogleDriveConnector()
        assert c.authenticate() is False

    def test_list_files_without_auth_raises(self):
        c = GoogleDriveConnector()
        assert not c.is_authenticated()
        try:
            c.list_files()
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass

    def test_download_without_auth_raises(self):
        c = GoogleDriveConnector()
        try:
            c.download("some-id")
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass


class TestMockMode:
    def test_authenticate_in_mock_mode(self, mock_mode):
        c = GoogleDriveConnector()
        assert c.authenticate() is True
        assert c.is_authenticated()

    def test_list_files_in_mock_mode(self, mock_mode):
        c = GoogleDriveConnector()
        c.authenticate()
        files, next_token = c.list_files()
        assert isinstance(files, list)
        assert len(files) >= 1
        assert files[0].id == "test-file-1"
        assert next_token is None

    def test_download_in_mock_mode(self, mock_mode):
        c = GoogleDriveConnector()
        c.authenticate()
        data = c.download("test-file-1")
        assert isinstance(data, bytes)
        assert len(data) > 0
        assert data == b"This is a test file."

    def test_ingest_in_mock_mode(self, mock_mode):
        c = GoogleDriveConnector()
        c.authenticate()
        doc = c.ingest("test-file-1")
        assert doc is not None
        assert doc.id == "test-file-1"
        assert doc.source_type == "google_drive"
        assert doc.title == "test.txt"
        assert doc.sha256 is not None
        assert doc.text_content == "This is a test file."


class TestRegistryIntegration:
    def test_registered_as_google_drive(self):
        from ingestao.connectors import get_connector, list_sources
        sources = list_sources()
        assert "google_drive" in sources
        c = get_connector("google_drive")
        assert isinstance(c, GoogleDriveConnector)


class TestMetadataExtraction:
    def test_extract_metadata_from_api_dict(self):
        c = GoogleDriveConnector()
        api_item = {
            "id": "abc123",
            "name": "report.pdf",
            "mimeType": "application/pdf",
            "size": "2048",
            "createdTime": "2025-01-15T10:30:00.000Z",
            "modifiedTime": "2025-01-16T14:00:00.000Z",
            "owners": [{"displayName": "Alice", "emailAddress": "alice@example.com"}],
            "lastModifyingUser": {"displayName": "Bob", "emailAddress": "bob@example.com"},
            "webViewLink": "https://drive.google.com/file/d/abc123",
            "parents": ["folder1"],
            "description": "Monthly report",
            "trashed": False,
        }
        doc = c.extract_metadata(api_item)
        assert doc.id == "abc123"
        assert doc.title == "report.pdf"
        assert doc.mime_type == "application/pdf"
        assert doc.author == "Bob"
        assert doc.timestamp is not None
        assert doc.timestamp.year == 2025
