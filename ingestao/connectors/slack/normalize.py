import hashlib
from datetime import datetime


def normalize_message(message):
    """Normalize a Slack message dict into a canonical Document-like dict.

    Expected minimal input: {'text': str, 'user': 'U123', 'ts': '1234567890.123'}
    """
    text = (message.get("text") or "").strip()
    ts = message.get("ts") or "0"
    channel = message.get("channel")
    author = message.get("user") or message.get("bot_id") or "unknown"

    sha256 = hashlib.sha256((text or "").encode("utf-8")).hexdigest()

    doc = {
        "id": f"slack:{channel}:{ts}",
        "source": "slack",
        "author": author,
        "timestamp": datetime.utcfromtimestamp(float(ts.split(".")[0])).isoformat() + "Z" if ts and ts != "0" else None,
        "text_excerpt": text[:500],
        "sha256": sha256,
        "channel": channel,
        "thread_ts": message.get("thread_ts"),
        "attachments": message.get("files") or [],
    }
    return doc
