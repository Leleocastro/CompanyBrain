import os
import sys
from ingestao.connectors.google_drive.client import GoogleDriveConnector

failed = 0

# Test 1
try:
    c = GoogleDriveConnector()
    assert c is not None
    print('test_connector_class_exists: OK')
except Exception as e:
    print('test_connector_class_exists: FAIL', e)
    failed += 1

# Test 2
try:
    c = GoogleDriveConnector()
    os.environ.pop('GDRIVE_TEST_MODE', None)
    try:
        c.list_files()
        raise AssertionError('Expected RuntimeError')
    except RuntimeError:
        print('test_list_files_without_auth_raises: OK')
except Exception as e:
    print('test_list_files_without_auth_raises: FAIL', e)
    failed += 1

# Test 3 (mock smoke)
try:
    os.environ['GDRIVE_TEST_MODE'] = 'mock'
    c = GoogleDriveConnector()
    c._client = False
    files = c.list_files()
    assert isinstance(files, list) and len(files) >= 1
    fid = files[0]['id']
    data = c.download_file(fid)
    assert isinstance(data, (bytes, bytearray)) and len(data) > 0
    print('test_smoke_list_and_download_mock_mode: OK')
    os.environ.pop('GDRIVE_TEST_MODE', None)
except Exception as e:
    print('test_smoke_list_and_download_mock_mode: FAIL', e)
    failed += 1

if failed:
    print(f"{failed} tests failed")
    sys.exit(2)
else:
    print('ALL TESTS PASSED')
    sys.exit(0)
