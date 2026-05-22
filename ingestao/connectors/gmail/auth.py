import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, Optional


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
DEFAULT_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailAuth:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: str = "http://localhost:8000/oauth2callback",
        scopes: Optional[list] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or DEFAULT_SCOPES

    @property
    def _scope_str(self) -> str:
        return " ".join(self.scopes)

    @property
    def _is_mock(self) -> bool:
        return not self.client_id or not self.client_secret

    def get_authorize_url(self, state: Optional[str] = None) -> str:
        params = {
            "client_id": self.client_id or "__MOCK_CLIENT_ID__",
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self._scope_str,
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code(self, code: str) -> Dict[str, str]:
        if self._is_mock:
            return {
                "access_token": "mock_access_token",
                "refresh_token": "mock_refresh_token",
                "expires_in": "3600",
            }
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        return self._post_token_request(data)

    def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        if self._is_mock:
            return {"access_token": "mock_refreshed_token", "expires_in": "3600"}
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        result = self._post_token_request(data)
        result.pop("refresh_token", None)
        return result

    def _post_token_request(self, data: Dict[str, str]) -> Dict[str, str]:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(GOOGLE_TOKEN_URL, data=body, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise RuntimeError(f"Token request failed: {e.code} {error_body}") from e
