"""PII detection and redaction."""

import re
from typing import List, Tuple


_REDACT_PATTERNS: List[Tuple[str, str]] = [
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),
]


def redact_pii(text: str) -> str:
    """Replace sensitive patterns with placeholders."""
    for pattern, replacement in _REDACT_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def has_pii(text: str) -> bool:
    """Check if text contains any known PII patterns."""
    for pattern, _ in _REDACT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False
