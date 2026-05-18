import os

from ingestao.connectors.google_drive.client import GoogleDriveConnector


def test_connector_class_exists():
    c = GoogleDriveConnector()
    assert c is not None


def test_list_files_without_auth_raises():
    c = GoogleDriveConnector()
    # ensure env test mode not set
    os.environ.pop('GDRIVE_TEST_MODE', None)
    raised = False
    try:
        c.list_files()
    except RuntimeError:
        raised = True
    assert raised


def test_smoke_list_and_download_mock_mode():
    # Smoke test using mock mode without real authentication
    os.environ['GDRIVE_TEST_MODE'] = 'mock'
    c = GoogleDriveConnector()
    # ensure client not set so mock path is taken
    c._client = False
    files = c.list_files()
    assert isinstance(files, list) and len(files) >= 1
    fid = files[0]['id']
    data = c.download_file(fid)
    assert isinstance(data, (bytes, bytearray)) and len(data) > 0
    os.environ.pop('GDRIVE_TEST_MODE', None)
