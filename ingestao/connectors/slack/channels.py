from ingestao.connectors.slack.client import SlackClient


def list_channels(client: SlackClient, limit: int = 200) -> list[dict]:
    channels = []
    cursor = None
    while True:
        params = {
            "types": "public_channel",
            "limit": min(limit, 200),
            "exclude_archived": True,
        }
        if cursor:
            params["cursor"] = cursor
        resp = client.conversations_list(**params)
        channels.extend(resp.get("channels", []))
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor or len(channels) >= limit:
            break
    return channels[:limit]
