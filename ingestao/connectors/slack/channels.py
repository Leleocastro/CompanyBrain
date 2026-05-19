"""Channels listing helper (public channels) - stub implementation.

This module provides a small API that higher-level code/tests can call.
"""

from .auth import SlackAuth
from .client import SlackClient


def list_channels(page_size=100):
    """Return a generator of mock channel dicts.

    In a real environment this calls Slack API (conversations.list) with pagination.
    """
    auth = SlackAuth()
    token = auth.bot_token
    if not token:
        # Return empty generator if token missing to avoid accidental API calls in test env.
        return
        yield  # pragma: no cover

    client = SlackClient(token)
    # Real implementation would iterate pages and yield channel objects
    raise NotImplementedError("list_channels requires slack_sdk.WebClient integration")
