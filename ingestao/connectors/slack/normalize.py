import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Document:
    id: str
    source: str
    author: str
    timestamp: datetime
    text_excerpt: str
    sha256: str
    channel: str
    thread_ts: str | None = None
    attachments: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ts_to_datetime(ts: str) -> datetime:
    return datetime.utcfromtimestamp(float(ts))


def normalize_message(
    raw: dict,
    channel_id: str,
    source: str = "slack",
) -> Document:
    ts = raw.get("ts", "0")
    text = raw.get("text", "") or ""
    user = raw.get("user", raw.get("bot_id", "unknown"))
    thread_ts = raw.get("thread_ts")
    attachments = raw.get("attachments") or []
    files = raw.get("files") or []

    return Document(
        id=f"{source}:{channel_id}:{ts}",
        source=source,
        author=user,
        timestamp=_ts_to_datetime(ts),
        text_excerpt=text[:500],
        sha256=_compute_sha256(text),
        channel=channel_id,
        thread_ts=thread_ts,
        attachments=[{"type": "file", **f} for f in files] + attachments,
        metadata={
            "raw_ts": ts,
            "has_thread": thread_ts is not None,
            "is_bot": raw.get("bot_id") is not None,
            "subtype": raw.get("subtype"),
        },
    )
