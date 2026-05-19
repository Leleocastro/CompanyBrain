"""Parsing & normalization for Gmail messages and threads.

Convert Gmail message structures into the project's canonical ingestion item shape.
"""
from typing import Dict, Any


def normalize_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a Gmail message dict into a canonical dict.

    Expected output keys: id, source, author, timestamp, text_excerpt, sha256
    """
    return {
        "id": msg.get("id"),
        "source": "gmail",
        "author": msg.get("from") or msg.get("sender"),
        "timestamp": msg.get("internalDate") or msg.get("date"),
        "text_excerpt": (msg.get("snippet") or "")[:512],
        "sha256": None,
    }


if __name__ == "__main__":
    print("Gmail parser scaffold loaded")
