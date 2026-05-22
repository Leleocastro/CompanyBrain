from ingestao.connectors.slack.client import SlackClient


def fetch_thread(
    client: SlackClient, channel_id: str, thread_ts: str, limit: int = 100
) -> list[dict]:
    messages = []
    cursor = None
    while True:
        params: dict = {
            "channel": channel_id,
            "ts": thread_ts,
            "limit": min(limit, 100),
        }
        if cursor:
            params["cursor"] = cursor
        resp = client.conversations_replies(**params)
        messages.extend(resp.get("messages", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor or len(messages) >= limit:
            break
    return messages[:limit]


def fetch_channel_history(
    client: SlackClient, channel_id: str, limit: int = 50
) -> list[dict]:
    messages = []
    cursor = None
    while True:
        params: dict = {
            "channel": channel_id,
            "limit": min(limit, 50),
        }
        if cursor:
            params["cursor"] = cursor
        resp = client.conversations_history(**params)
        messages.extend(resp.get("messages", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor or len(messages) >= limit:
            break
    return messages[:limit]
