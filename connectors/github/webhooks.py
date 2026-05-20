"""Webhook handler utilities for GitHub connector (MVP).
Provides simple HMAC-SHA256 signature verification compatible with GitHub webhooks.
"""
import hmac
import hashlib
from typing import Optional


def verify_signature(secret: str, signature_header: str, body: bytes) -> bool:
    """Verify the X-Hub-Signature-256 header value.
    header example: 'sha256=...'"""
    if not signature_header:
        return False
    try:
        algo, signature = signature_header.split("=", 1)
    except ValueError:
        return False
    if algo != "sha256":
        return False
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature)
