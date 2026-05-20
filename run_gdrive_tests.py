#!/usr/bin/env python3
"""Standalone test runner for the Google Drive connector (no pytest required)."""

import os
import sys

from ingestao.connectors.google_drive.client import GoogleDriveConnector

failed = 0

os.environ.setdefault("GDRIVE_TEST_MODE", "mock")


# Test 1
try:
    c = GoogleDriveConnector()
    assert c is not None
    print("test_connector_class_exists: OK")
except Exception as e:
    print("test_connector_class_exists: FAIL", e)
    failed += 1


# Test 2: authenticate in mock mode
try:
    c = GoogleDriveConnector()
    ok = c.authenticate()
    assert ok is True
    assert c.is_authenticated()
    print("test_authenticate_mock: OK")
except Exception as e:
    print("test_authenticate_mock: FAIL", e)
    failed += 1


# Test 3: list_files in mock mode
try:
    c = GoogleDriveConnector()
    c.authenticate()
    files, next_token = c.list_files()
    assert isinstance(files, list) and len(files) >= 1
    assert files[0].id == "test-file-1"
    assert next_token is None
    print("test_list_files_mock: OK")
except Exception as e:
    print("test_list_files_mock: FAIL", e)
    failed += 1


# Test 4: download in mock mode
try:
    c = GoogleDriveConnector()
    c.authenticate()
    data = c.download("test-file-1")
    assert isinstance(data, bytes) and len(data) > 0
    assert data == b"This is a test file."
    print("test_download_mock: OK")
except Exception as e:
    print("test_download_mock: FAIL", e)
    failed += 1


# Test 5: ingest pipeline in mock mode
try:
    c = GoogleDriveConnector()
    c.authenticate()
    doc = c.ingest("test-file-1")
    assert doc is not None
    assert doc.id == "test-file-1"
    assert doc.source_type == "google_drive"
    assert doc.sha256 is not None
    print("test_ingest_mock: OK")
except Exception as e:
    print("test_ingest_mock: FAIL", e)
    failed += 1


if failed:
    print(f"{failed} tests failed")
    sys.exit(2)
else:
    print("ALL TESTS PASSED")
    sys.exit(0)
