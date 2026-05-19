import os

class SlackAuth:
    """Simple auth helper — reads SLACK_BOT_TOKEN from the environment."""
    def __init__(self):
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN")

    def require_token(self):
        if not self.bot_token:
            raise RuntimeError("SLACK_BOT_TOKEN environment variable is required for Slack connector")
        return self.bot_token
