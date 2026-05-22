import base64
import hashlib
import json
from typing import Any, Dict, List, Optional


def normalize_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    headers = _extract_headers(msg.get("payload", {}))
    body_preview = _extract_body_preview(msg.get("payload", {}))

    author_raw = headers.get("From", "")
    return {
        "id": msg.get("id"),
        "thread_id": msg.get("threadId"),
        "source": "gmail",
        "author": _clean_email(author_raw),
        "author_raw": author_raw,
        "recipients": [
            _clean_email(r) for r in headers.get("To", "").split(",") if r.strip()
        ]
        if headers.get("To")
        else [],
        "subject": headers.get("Subject"),
        "timestamp": msg.get("internalDate"),
        "date": headers.get("Date"),
        "text_excerpt": (msg.get("snippet") or body_preview or "")[:512],
        "label_ids": msg.get("labelIds", []),
        "attachments": _extract_attachments(msg.get("payload", {})),
        "sha256": _compute_sha256(msg),
    }


def normalize_thread(thread: Dict[str, Any]) -> Dict[str, Any]:
    messages = thread.get("messages", [])
    normalized_messages = [normalize_message(m) for m in messages]
    return {
        "id": thread.get("id"),
        "source": "gmail",
        "message_count": len(normalized_messages),
        "messages": normalized_messages,
        "sha256": (
            hashlib.sha256(
                json.dumps(
                    [m["id"] for m in normalized_messages], sort_keys=True
                ).encode()
            ).hexdigest()
            if normalized_messages
            else None
        ),
    }


def _extract_headers(payload: Dict[str, Any]) -> Dict[str, str]:
    headers = {}
    for h in payload.get("headers", []):
        name = h.get("name", "")
        if name:
            headers[name] = h.get("value", "")
    return headers


def _extract_body_preview(payload: Dict[str, Any]) -> str:
    if payload.get("mimeType") == "text/plain":
        body_data = payload.get("body", {}).get("data", "")
        if body_data:
            try:
                return base64.urlsafe_b64decode(body_data).decode(
                    "utf-8", errors="replace"
                )
            except Exception:
                return ""
    for part in payload.get("parts", []):
        result = _extract_body_preview(part)
        if result:
            return result
    return ""


def _extract_attachments(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    attachments = []
    if payload.get("filename"):
        body = payload.get("body", {})
        if body.get("attachmentId"):
            attachments.append(
                {
                    "filename": payload["filename"],
                    "mime_type": payload.get("mimeType"),
                    "attachment_id": body["attachmentId"],
                    "size": body.get("size", 0),
                }
            )
    for part in payload.get("parts", []):
        attachments.extend(_extract_attachments(part))
    return attachments


def _compute_sha256(msg: Dict[str, Any]) -> Optional[str]:
    raw = json.dumps(msg, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _clean_email(raw: str) -> str:
    if "<" in raw and ">" in raw:
        return raw.split("<")[1].rstrip(">")
    return raw.strip()
