import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GmailConfig:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: str = "http://localhost:8000/oauth2callback"
    scopes: list = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/gmail.readonly",
    ])
    token_path: Optional[str] = None
    max_results: int = 20

    @classmethod
    def from_env(cls) -> "GmailConfig":
        return cls(
            client_id=os.environ.get("GMAIL_CLIENT_ID"),
            client_secret=os.environ.get("GMAIL_CLIENT_SECRET"),
            redirect_uri=os.environ.get(
                "GMAIL_OAUTH_REDIRECT", "http://localhost:8000/oauth2callback"
            ),
            token_path=os.environ.get("GMAIL_TOKEN_PATH"),
            max_results=int(os.environ.get("GMAIL_MAX_RESULTS", "20")),
        )


def get_config() -> dict:
    cfg = GmailConfig.from_env()
    return {
        "GMAIL_CLIENT_ID": cfg.client_id,
        "GMAIL_CLIENT_SECRET": cfg.client_secret,
        "GMAIL_OAUTH_REDIRECT": cfg.redirect_uri,
        "GMAIL_SCOPES": cfg.scopes,
        "GMAIL_TOKEN_PATH": cfg.token_path,
        "GMAIL_MAX_RESULTS": cfg.max_results,
    }
