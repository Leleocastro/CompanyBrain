"""Google Drive connector with OAuth and Service Account authentication."""

import io
import json
import logging
import os
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

from ingestao.connectors.base import BaseConnector, Document
from ingestao.connectors.google_drive.models import DriveFile
from ingestao.connectors.google_drive.normalizer import drive_file_to_document
from ingestao.connectors import register

logger = logging.getLogger(__name__)

_GDRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]

_DEFAULT_PAGE_SIZE = 100
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0


def _try_import_google() -> Tuple[bool, str]:
    """Check if google API libraries are available. Returns (available, reason)."""
    try:
        import google.auth  # noqa: F401
        import google.oauth2.credentials  # noqa: F401
        import google.oauth2.service_account  # noqa: F401
        import googleapiclient.discovery  # noqa: F401
        import googleapiclient.errors  # noqa: F401
        import googleapiclient.http  # noqa: F401
        return True, ""
    except ImportError as exc:
        return False, str(exc)


def _build_drive_service(credentials):
    from googleapiclient.discovery import build
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _parse_credentials_json(raw: str) -> dict:
    return json.loads(raw)


@register("google_drive")
class GoogleDriveConnector(BaseConnector):
    """Google Drive connector.

    Two authentication modes:
      1. **OAuth** – each user authorizes their own Google Drive.
         Pass an OAuth 2.0 token via ``credentials`` or set
         ``GDRIVE_OAUTH_TOKEN`` env var (JSON-serialized
         ``google.oauth2.credentials.Credentials``).

      2. **Service Account** – domain-wide delegation.
         Set ``GDRIVE_SA_KEYFILE`` env var pointing to a JSON key file,
         or pass ``sa_keyfile_path`` / ``sa_keyfile_dict``.

    When neither auth source is available the connector falls back to
    **mock mode** (driven by ``GDRIVE_TEST_MODE=mock``) so tests pass
    without real credentials.

    Args:
        credentials: An already-built ``google.oauth2.credentials.Credentials``
            object (OAuth path).  Overrides env vars.
        sa_keyfile_path: Path to a service-account JSON key file.
        sa_keyfile_dict: Service-account key as a ``dict``.
        page_size: Number of items per Drive API page (default 100).
    """

    def __init__(
        self,
        credentials=None,
        sa_keyfile_path: Optional[str] = None,
        sa_keyfile_dict: Optional[dict] = None,
        page_size: int = _DEFAULT_PAGE_SIZE,
    ):
        self._service = None
        self._auth_method: Optional[str] = None
        self._page_size = page_size
        self._google_available, self._import_err = _try_import_google()

        self._injected_credentials = credentials
        self._sa_keyfile_path = sa_keyfile_path
        self._sa_keyfile_dict = sa_keyfile_dict

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """Authenticate against Google Drive.

        Resolution order:
          1. Injected ``credentials`` object (OAuth).
          2. ``GDRIVE_OAUTH_TOKEN`` env var (OAuth).
          3. ``sa_keyfile_path`` / ``sa_keyfile_dict`` / ``GDRIVE_SA_KEYFILE``
             (service account).
          4. ``GDRIVE_TEST_MODE=mock`` – no-op, returns ``True``.

        Returns:
            ``True`` if authenticated (or mock mode), ``False`` otherwise.
        """
        if self._service is not None:
            return True

        creds = self._resolve_credentials()
        if creds is None:
            if os.environ.get("GDRIVE_TEST_MODE") == "mock":
                self._auth_method = "mock"
                logger.info("GoogleDriveConnector: mock mode – skipping real auth")
                return True
            logger.warning("GoogleDriveConnector: no credentials available")
            return False

        if not self._google_available:
            logger.error(
                "GoogleDriveConnector: google-api-python-client not installed (%s)",
                self._import_err,
            )
            return False

        try:
            self._service = _build_drive_service(creds)
            # Ping the API to confirm the token works
            self._service.about().get(fields="user").execute()
            logger.info("GoogleDriveConnector: authenticated (%s)", self._auth_method)
            return True
        except Exception as exc:
            logger.error("GoogleDriveConnector: auth failed: %s", exc)
            self._service = None
            return False

    def _resolve_credentials(self):
        """Return a credentials object or None."""
        # 1. Injected OAuth credentials
        if self._injected_credentials is not None:
            self._auth_method = "oauth"
            return self._injected_credentials

        # 2. OAuth token from env
        token_json = os.environ.get("GDRIVE_OAUTH_TOKEN")
        if token_json:
            from google.oauth2.credentials import Credentials
            self._auth_method = "oauth"
            return Credentials.from_authorized_user_info(
                _parse_credentials_json(token_json), _GDRIVE_SCOPES
            )

        # 3. Service account via parameter or env
        sa_info = self._sa_keyfile_dict
        if sa_info is None:
            key_path = (
                self._sa_keyfile_path
                or os.environ.get("GDRIVE_SA_KEYFILE")
            )
            if key_path and os.path.exists(key_path):
                with open(key_path) as f:
                    sa_info = json.load(f)

        if sa_info is not None:
            from google.oauth2.service_account import Credentials as SACredentials
            self._auth_method = "service_account"
            return SACredentials.from_service_account_info(
                sa_info, scopes=_GDRIVE_SCOPES
            )

        return None

    def is_authenticated(self) -> bool:
        return self._service is not None or self._auth_method == "mock"

    # ------------------------------------------------------------------
    # Core API operations
    # ------------------------------------------------------------------

    def list_files(
        self,
        query: Optional[str] = None,
        page_token: Optional[str] = None,
    ) -> Tuple[List[DriveFile], Optional[str]]:
        """List files matching the query.

        Args:
            query: Drive API ``q`` parameter.  When ``None``, all non-trashed
                files the authenticated user has access to are returned.
            page_token: Token for the next page (pagination).

        Returns:
            ``(files, next_page_token)``.
        """
        if self._auth_method == "mock":
            return self._mock_list_files(query), None

        self._ensure_service()

        q = query or "trashed=false"
        try:
            request = self._service.files().list(
                q=q,
                pageSize=self._page_size,
                pageToken=page_token,
                fields="nextPageToken, files(id, name, mimeType, size, "
                       "createdTime, modifiedTime, owners, lastModifyingUser, "
                       "webViewLink, parents, description, trashed)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            response = self._execute_with_retry(request)
            items = response.get("files", [])
            files = [DriveFile.from_api(item) for item in items]
            return files, response.get("nextPageToken")
        except Exception as exc:
            logger.error("GoogleDriveConnector: list_files failed: %s", exc)
            raise

    def list_all_files(self, query: Optional[str] = None) -> List[DriveFile]:
        """Convenience: iterate all pages and return every file."""
        all_files: List[DriveFile] = []
        token: Optional[str] = None
        while True:
            batch, token = self.list_files(query=query, page_token=token)
            all_files.extend(batch)
            if not token:
                break
        return all_files

    def download(self, file_id: str) -> bytes:
        """Download a file's binary content by its Drive file ID.

        For Google-native formats (Docs, Sheets, Slides, etc.) the method
        exports to a standard format (PDF / plain text / CSV / PPTX).
        """
        if self._auth_method == "mock":
            return self._mock_download(file_id)

        self._ensure_service()

        file_meta = self._get_file_meta(file_id)
        mime = file_meta.get("mimeType", "")

        try:
            if mime.startswith("application/vnd.google-apps."):
                return self._export_google_native(file_id, mime)
            return self._download_binary(file_id)
        except Exception as exc:
            logger.error("GoogleDriveConnector: download(%s) failed: %s", file_id, exc)
            raise

    def _download_binary(self, file_id: str) -> bytes:
        request = self._service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        from googleapiclient.http import MediaIoBaseDownload
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return fh.getvalue()

    def _export_google_native(self, file_id: str, mime: str) -> bytes:
        _MIME_EXPORT_MAP = {
            "application/vnd.google-apps.document": "text/plain",
            "application/vnd.google-apps.spreadsheet": "text/csv",
            "application/vnd.google-apps.presentation": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.google-apps.drawing": "image/png",
            "application/vnd.google-apps.script": "application/vnd.google-apps.script+json",
        }
        export_mime = _MIME_EXPORT_MAP.get(mime)
        if not export_mime:
            logger.warning("GoogleDriveConnector: unsupported Google-native type %s, falling back to PDF", mime)
            export_mime = "application/pdf"

        request = self._service.files().export(fileId=file_id, mimeType=export_mime)
        from googleapiclient.http import MediaIoBaseDownload
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return fh.getvalue()

    # ------------------------------------------------------------------
    # Metadata extraction
    # ------------------------------------------------------------------

    def extract_metadata(self, file_info: dict) -> Document:
        """Build a ``Document`` from a Drive API file info dict."""
        df = DriveFile.from_api(file_info)
        return drive_file_to_document(df)

    def get_file_meta(self, file_id: str) -> dict:
        return self._get_file_meta(file_id)

    def _get_file_meta(self, file_id: str) -> dict:
        self._ensure_service()
        try:
            return self._service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, "
                       "owners, lastModifyingUser, webViewLink, description",
                supportsAllDrives=True,
            ).execute()
        except Exception as exc:
            logger.error("GoogleDriveConnector: get_file_meta(%s) failed: %s", file_id, exc)
            raise

    # ------------------------------------------------------------------
    # Full ingest pipeline
    # ------------------------------------------------------------------

    def ingest(self, file_id: str) -> Optional[Document]:
        """Download a file, extract text, normalize metadata, redact PII.

        Returns a ``Document`` ready for forwarding to the indexer, or
        ``None`` on failure.
        """
        try:
            if self._auth_method == "mock":
                mock_files = self._mock_list_files(None)
                matched = [f for f in mock_files if f.id == file_id]
                df = matched[0] if matched else DriveFile(id=file_id, name=file_id, mime_type="text/plain")
                raw = self._mock_download(file_id)
                text_content = self._try_decode_text(raw, df.mime_type)
                doc = drive_file_to_document(df, raw_bytes=raw, text_content=text_content)
                return doc
            meta = self._get_file_meta(file_id)
            raw = self.download(file_id)
            text_content = self._try_decode_text(raw, meta.get("mimeType", ""))
            df = DriveFile.from_api(meta)
            doc = drive_file_to_document(df, raw_bytes=raw, text_content=text_content)
            return doc
        except Exception as exc:
            logger.error("GoogleDriveConnector: ingest(%s) failed: %s", file_id, exc)
            return None

    @staticmethod
    def _try_decode_text(data: bytes, mime_type: str) -> str:
        if mime_type.startswith("text/"):
            return data.decode("utf-8", errors="replace")
        try:
            return data.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            return ""

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    def _execute_with_retry(self, request):
        from googleapiclient.errors import HttpError
        last_exc = None
        for attempt in range(_MAX_RETRIES):
            try:
                return request.execute()
            except HttpError as exc:
                last_exc = exc
                if exc.resp.status in (429, 500, 502, 503):
                    sleep_for = _BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "GoogleDriveConnector: retry %d/%d after %s (status=%d)",
                        attempt + 1, _MAX_RETRIES, sleep_for, exc.resp.status,
                    )
                    time.sleep(sleep_for)
                    continue
                raise
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_service(self):
        if self._service is None:
            raise RuntimeError(
                "GoogleDriveConnector: not authenticated. Call authenticate() first."
            )

    # ------------------------------------------------------------------
    # Mock helpers (for testing without real credentials)
    # ------------------------------------------------------------------

    def _mock_list_files(self, query: Optional[str] = None) -> List[DriveFile]:
        return [
            DriveFile(
                id="test-file-1",
                name="test.txt",
                mime_type="text/plain",
                size=17,
                owners=["test@example.com"],
            ),
        ]

    @staticmethod
    def _mock_download(file_id: str) -> bytes:
        if file_id == "test-file-1":
            return b"This is a test file."
        return b""
