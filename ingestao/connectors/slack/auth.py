import os


class SlackAuth:
    def __init__(self, token: str | None = None):
        self._token = token or os.environ.get("SLACK_BOT_TOKEN")
        if not self._token:
            raise ValueError(
                "SLACK_BOT_TOKEN is required. Set it via env var or pass token=."
            )

    @property
    def token(self) -> str:
        return self._token  # pragma: no cover

    @classmethod
    def from_env(cls) -> "SlackAuth":
        return cls()
