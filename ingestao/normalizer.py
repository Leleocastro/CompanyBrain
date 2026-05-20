"""Generic metadata normalization utilities."""

import hashlib
from datetime import datetime
from typing import Optional


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_timestamp(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None
