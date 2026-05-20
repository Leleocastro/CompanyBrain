"""Abstract base class for all connectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Document:
    """Normalized document produced by every connector."""
    id: str
    source: str
    source_type: str
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    title: Optional[str] = None
    mime_type: str = "application/octet-stream"
    text_content: Optional[str] = None
    raw_bytes: Optional[bytes] = None
    sha256: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseConnector(ABC):
    """Every source connector must subclass this."""

    @abstractmethod
    def authenticate(self) -> bool:
        ...

    @abstractmethod
    def list_files(self, query: Optional[str] = None) -> List[dict]:
        ...

    @abstractmethod
    def download(self, file_id: str) -> bytes:
        ...

    @abstractmethod
    def extract_metadata(self, file_info: dict) -> Document:
        ...

    def ingest(self, file_id: str) -> Optional[Document]:
        """High-level pipeline: download → extract → normalize."""
        raise NotImplementedError
