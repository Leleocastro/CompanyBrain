from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AuthType(Enum):
    OAUTH = "oauth"
    GITHUB_APP = "github_app"
    PAT = "pat"


@dataclass
class AuthConfig:
    auth_type: AuthType
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorization_code: Optional[str] = None
    app_id: Optional[str] = None
    private_key: Optional[str] = None
    installation_id: Optional[str] = None
    personal_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> AuthConfig:
        if token := os.environ.get("GITHUB_TOKEN"):
            return cls(auth_type=AuthType.PAT, personal_token=token)

        if os.environ.get("GITHUB_APP_ID"):
            return cls(
                auth_type=AuthType.GITHUB_APP,
                app_id=os.environ["GITHUB_APP_ID"],
                private_key=os.environ.get("GITHUB_PRIVATE_KEY"),
                installation_id=os.environ.get("GITHUB_INSTALLATION_ID"),
            )

        return cls(
            auth_type=AuthType.OAUTH,
            client_id=os.environ.get("GITHUB_CLIENT_ID"),
            client_secret=os.environ.get("GITHUB_CLIENT_SECRET"),
        )

    @classmethod
    def from_user_token(cls, token: str) -> AuthConfig:
        return cls(auth_type=AuthType.PAT, personal_token=token)

    @classmethod
    def from_oauth_code(
        cls, code: str, client_id: str, client_secret: str
    ) -> AuthConfig:
        return cls(
            auth_type=AuthType.OAUTH,
            client_id=client_id,
            client_secret=client_secret,
            authorization_code=code,
        )


class GitHubAuth:
    def __init__(self, config: AuthConfig) -> None:
        self.config = config
        self._token: Optional[str] = None

    async def authenticate(self) -> str:
        if self.config.auth_type == AuthType.PAT:
            self._token = self.config.personal_token
        elif self.config.auth_type == AuthType.GITHUB_APP:
            self._token = await self._get_app_token()
        elif self.config.auth_type == AuthType.OAUTH:
            self._token = await self._get_oauth_token()
        else:
            raise ValueError(f"Unknown auth type: {self.config.auth_type}")

        return self._token

    async def _get_app_token(self) -> str:
        import time

        import jwt

        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": self.config.app_id,
        }
        jwt_token = jwt.encode(payload, self.config.private_key, algorithm="RS256")

        import httpx

        async with httpx.AsyncClient() as client:
            url = (
                f"https://api.github.com/app/installations/"
                f"{self.config.installation_id}/access_tokens"
            )
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            resp.raise_for_status()
            return resp.json()["token"]

    async def _get_oauth_token(self) -> str:
        if not self.config.authorization_code:
            raise ValueError(
                "authorization_code is required for OAuth token exchange. "
                "The end-user must complete the GitHub OAuth web flow first."
            )

        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                json={
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "code": self.config.authorization_code,
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]
