"""Simple OAuth/PAT scaffolding for GitHub connector (MVP).
This module provides minimal, framework-style helpers used in tests and
by higher-level code. Real implementations should handle HTTP requests,
secure storage, token refresh, and error handling.
"""
from typing import Optional

class GitHubAuth:
    def __init__(self, token: str, token_type: str = "bearer"):
        self.token = token
        self.token_type = token_type

    @classmethod
    def from_pat(cls, pat: str) -> "GitHubAuth":
        """Create auth instance from a Personal Access Token (PAT).
        PATs are useful for CLI / testing flows in the MVP.
        """
        return cls(token=pat, token_type="token")

    @classmethod
    def from_oauth_code(cls, client_id: str, client_secret: str, code: str) -> "GitHubAuth":
        """Placeholder for exchange of authorization code -> access token.
        In the real system this performs an HTTP POST to GitHub's /login/oauth/access_token.
        For MVP scaffolding we return a dummy token derived from inputs (no network calls).
        """
        token = f"oauth_dummy_{client_id[:6]}_{code[:6]}"
        return cls(token=token, token_type="bearer")

    def authorization_header(self) -> str:
        if self.token_type == "token":
            return f"token {self.token}"
        return f"Bearer {self.token}"
