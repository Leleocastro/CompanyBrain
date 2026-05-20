"""Shared data models for ingestion pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SourceDocument:
    """Payload forwarded to the indexer agent."""
    id: str
    source: str
    source_type: str
    author: Optional[str] = None
    timestamp: Optional[datetime] = None
    title: Optional[str] = None
    mime_type: str = "application/octet-stream"
    text_excerpt: Optional[str] = None
    sha256: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    pii_redacted: bool = False
