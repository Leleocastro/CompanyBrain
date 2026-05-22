from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import httpx
import jwt

logger = logging.getLogger(__name__)


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
    private_key: Optional[str] = field(default=None, repr=False)
    private_key_path: Optional[str] = None
    installation_id: Optional[str] = None
    personal_token: Optional[str] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.private_key_path and not self.private_key:
            with open(self.private_key_path) as f:
                self.private_key = f.read()

    @classmethod
    def from_env(cls) -> AuthConfig:
        if token := os.environ.get("GITHUB_TOKEN"):
            return cls(auth_type=AuthType.PAT, personal_token=token)

        if os.environ.get("GITHUB_APP_ID"):
            pk = os.environ.get("GITHUB_PRIVATE_KEY")
            pk_path = os.environ.get("GITHUB_PRIVATE_KEY_PATH")
            return cls(
                auth_type=AuthType.GITHUB_APP,
                app_id=os.environ["GITHUB_APP_ID"],
                private_key=pk,
                private_key_path=pk_path,
                installation_id=os.environ.get("GITHUB_INSTALLATION_ID"),
            )

        logger.warning(
            "No GITHUB_TOKEN, GITHUB_APP_ID, GITHUB_CLIENT_ID, or "
            "GITHUB_CLIENT_SECRET set — falling back to empty OAuth config"
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
    def __init__(
        self, config: AuthConfig, http_client: Optional[httpx.AsyncClient] = None
    ) -> None:
        self.config = config
        self._token: Optional[str] = None
        self._http = http_client

    async def _client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=30)
        return self._http

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

        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + 600,
            "iss": self.config.app_id,
        }

        if not self.config.private_key:
            raise ValueError("private_key is required for GitHub App authentication")
        jwt_token = jwt.encode(payload, self.config.private_key, algorithm="RS256")

        http = await self._client()
        url = (
            f"https://api.github.com/app/installations/"
            f"{self.config.installation_id}/access_tokens"
        )
        resp = await http.post(
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

        http = await self._client()
        resp = await http.post(
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

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
