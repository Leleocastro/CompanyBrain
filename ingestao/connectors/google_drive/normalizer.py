"""Metadata normalizer for Google Drive documents."""

from ingestao.connectors.base import Document
from ingestao.connectors.google_drive.models import DriveFile
from ingestao.normalizer import compute_sha256
from ingestao.pii import redact_pii


def drive_file_to_document(
    drive_file: DriveFile,
    raw_bytes: bytes = b"",
    text_content: str = "",
) -> Document:
    sha = compute_sha256(raw_bytes) if raw_bytes else None
    return Document(
        id=drive_file.id,
        source=f"google_drive:{drive_file.id}",
        source_type="google_drive",
        author=drive_file.last_modifying_user or (drive_file.owners[0] if drive_file.owners else None),
        timestamp=drive_file.modified_time or drive_file.created_time,
        title=drive_file.name,
        mime_type=drive_file.mime_type,
        text_content=redact_pii(text_content) if text_content else None,
        raw_bytes=raw_bytes if raw_bytes else None,
        sha256=sha,
        metadata={
            "size": drive_file.size,
            "created_time": drive_file.created_time.isoformat() if drive_file.created_time else None,
            "modified_time": drive_file.modified_time.isoformat() if drive_file.modified_time else None,
            "owners": drive_file.owners,
            "web_view_link": drive_file.web_view_link,
            "parents": drive_file.parents,
            "description": drive_file.description,
            "trashed": drive_file.trashed,
        },
    )
