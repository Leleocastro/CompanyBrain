import os
from typing import List, Optional

class GoogleDriveConnector:
    """Minimal Google Drive connector skeleton.

    Methods:
    - authenticate_service_account(keyfile_path)
    - authenticate_oauth(credentials)
    - list_files(q: Optional[str]=None) -> List[dict]
    - download_file(file_id: str) -> bytes
    """
    def __init__(self):
        self._client = None
        self._auth_method = None

    def authenticate_service_account(self, keyfile_path: str):
        if not os.path.exists(keyfile_path):
            raise FileNotFoundError("Service account keyfile not found: %s" % keyfile_path)
        # Placeholder: real implementation should build googleapiclient.discovery.Resource
        self._auth_method = 'service_account'
        self._client = True
        return True

    def authenticate_oauth(self, credentials: object):
        # Placeholder for OAuth credential handling
        if credentials is None:
            raise ValueError("credentials must be provided for OAuth authentication")
        self._auth_method = 'oauth'
        self._client = True
        return True

    def list_files(self, q: Optional[str] = None) -> List[dict]:
        """List files. In the skeleton implementation, if a real client is not available,
        attempt a smoke behavior driven by environment variable GDRIVE_TEST_MODE.
        """
        if not self._client:
            # If in test mode, return a fake file list so smoke tests can pass without API calls
            if os.environ.get('GDRIVE_TEST_MODE') == 'mock':
                return [{
                    'id': 'test-file-1',
                    'name': 'test.txt',
                    'mimeType': 'text/plain',
                    'owners': ['test@example.com']
                }]
            raise RuntimeError('Not authenticated with Google Drive')
        # Real implementation would call the Drive API here
        return []

    def download_file(self, file_id: str) -> bytes:
        if not self._client:
            if os.environ.get('GDRIVE_TEST_MODE') == 'mock' and file_id == 'test-file-1':
                return b"This is a test file."
            raise RuntimeError('Not authenticated with Google Drive')
        # Real implementation would stream and return bytes
        return b''
