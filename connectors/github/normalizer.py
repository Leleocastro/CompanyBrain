"""Normalization helpers to produce a canonical document shape used by the indexer.
Required fields (MVP): id_origem, source, author, timestamp, channel/path, excerpt, sha256
"""
from hashlib import sha256
from datetime import datetime
from typing import Dict, Any


def normalize_event(source: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a normalized document from a GitHub payload-ish dict.
    This function is intentionally forgiving and used by unit tests.
    """
    id_origem = payload.get("id") or payload.get("sha") or payload.get("full_name")
    author = None
    if "author" in payload and isinstance(payload["author"], dict):
        author = payload["author"].get("login")
    elif "user" in payload and isinstance(payload["user"], dict):
        author = payload["user"].get("login")

    excerpt = payload.get("message") or payload.get("title") or str(payload)
    timestamp = payload.get("timestamp") or datetime.utcnow().isoformat() + "Z"

    raw = f"{source}|{id_origem}|{excerpt}".encode("utf-8")
    digest = sha256(raw).hexdigest()

    return {
        "id_origem": str(id_origem),
        "source": source,
        "author": author,
        "timestamp": timestamp,
        "channel/path": payload.get("repo") or payload.get("full_name"),
        "excerpt": excerpt,
        "sha256": digest,
        "raw_payload": payload,
    }
