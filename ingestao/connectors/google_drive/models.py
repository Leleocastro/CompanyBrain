"""Data models for Google Drive files."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from ingestao.normalizer import safe_timestamp


@dataclass
class DriveFile:
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    created_time: Optional[datetime] = None
    modified_time: Optional[datetime] = None
    owners: List[str] = field(default_factory=list)
    last_modifying_user: Optional[str] = None
    web_view_link: Optional[str] = None
    parents: List[str] = field(default_factory=list)
    description: Optional[str] = None
    sha256: Optional[str] = None
    trashed: bool = False

    @classmethod
    def from_api(cls, item: dict) -> "DriveFile":
        owners = []
        for o in item.get("owners", []):
            name = o.get("displayName") or o.get("emailAddress") or ""
            if name:
                owners.append(name)
        return cls(
            id=item["id"],
            name=item.get("name", ""),
            mime_type=item.get("mimeType", "application/octet-stream"),
            size=int(item.get("size", 0)) if item.get("size") else None,
            created_time=safe_timestamp(item.get("createdTime")),
            modified_time=safe_timestamp(item.get("modifiedTime")),
            owners=owners,
            last_modifying_user=(
                item.get("lastModifyingUser", {})
                .get("displayName")
                or item.get("lastModifyingUser", {})
                .get("emailAddress")
            ),
            web_view_link=item.get("webViewLink"),
            parents=item.get("parents", []),
            description=item.get("description"),
            trashed=item.get("trashed", False),
        )
