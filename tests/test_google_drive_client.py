import os
import pytest

from ingestao.connectors.google_drive.client import GoogleDriveConnector


def test_connector_class_exists():
    c = GoogleDriveConnector()
    assert c is not None


def test_list_files_without_auth_raises():
    c = GoogleDriveConnector()
    # ensure env test mode not set
    os.environ.pop('GDRIVE_TEST_MODE', None)
    try:
        c.list_files()
        raised = False
    except RuntimeError:
        raised = True
    assert raised


@pytest.mark.skipif(os.environ.get('GDRIVE_TEST_MODE') != 'mock', reason='Integration smoke test skipped unless GDRIVE_TEST_MODE=mock')
def test_smoke_list_and_download():
    c = GoogleDriveConnector()
    # enable mock auth by faking the client
    c._client = True
    files = c.list_files()
    assert isinstance(files, list) and len(files) >= 1
    fid = files[0]['id']
    data = c.download_file(fid)
    assert isinstance(data, (bytes, bytearray)) and len(data) > 0
