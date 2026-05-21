import logging
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ingestao.connectors.slack.auth import SlackAuth

logger = logging.getLogger(__name__)


class SlackClient:
    def __init__(self, auth: SlackAuth | None = None):
        self._auth = auth or SlackAuth.from_env()
        self._client = WebClient(token=self._auth.token)
        self._retries = 3

    def _call(self, method: str, **kwargs):
        last_error = None
        for attempt in range(self._retries):
            try:
                api_method = getattr(self._client, method, None)
                if api_method is None:
                    api_method = self._client.api_call(method, **kwargs)
                resp = api_method(**kwargs)
                if not resp["ok"]:
                    raise SlackApiError(
                        f"Slack API returned ok=False: {resp.get('error', 'unknown')}",
                        resp,
                    )
                return resp
            except SlackApiError as e:
                error_code = e.response.get("error", "unknown")
                if error_code == "ratelimited":
                    retry_after = int(
                        e.response.headers.get("Retry-After", 5)
                    )
                    time.sleep(retry_after)
                    last_error = e
                    continue
                logger.error("Slack API error (attempt %d/%d): %s", attempt + 1, self._retries, error_code)
                raise
        raise last_error or RuntimeError("max retries exceeded")

    def conversations_list(self, **kwargs):
        return self._call("conversations_list", **kwargs)

    def conversations_history(self, **kwargs):
        return self._call("conversations_history", **kwargs)

    def conversations_replies(self, **kwargs):
        return self._call("conversations_replies", **kwargs)
