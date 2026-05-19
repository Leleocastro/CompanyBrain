"""Thread and channel history fetching helpers (stubs).

Provide clear function signatures so unit tests can import them without network access.
"""
from .auth import SlackAuth
from .client import SlackClient


def fetch_channel_history(channel_id, limit=200):
    """Fetch messages in a channel. Returns list of message dicts.

    Real impl: conversations.history with pagination.
    """
    auth = SlackAuth()
    if not auth.bot_token:
        return []
    client = SlackClient(auth.bot_token)
    raise NotImplementedError("fetch_channel_history requires slack_sdk integration")


def fetch_thread(channel_id, thread_ts):
    """Fetch thread replies given channel and thread timestamp."""
    auth = SlackAuth()
    if not auth.bot_token:
        return []
    client = SlackClient(auth.bot_token)
    raise NotImplementedError("fetch_thread requires slack_sdk integration")
