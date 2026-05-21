import os
import tempfile

import pytest

from ingestao.github_connector.auth import AuthConfig, AuthType, GitHubAuth


class TestAuthConfig:
    def test_from_env_missing(self, monkeypatch):
        for k in ["GITHUB_TOKEN", "GITHUB_APP_ID", "GITHUB_CLIENT_ID"]:
            monkeypatch.delenv(k, raising=False)
        config = AuthConfig.from_env()
        assert config.auth_type == AuthType.OAUTH
        assert config.client_id is None

    def test_from_env_pat(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_abc")
        config = AuthConfig.from_env()
        assert config.auth_type == AuthType.PAT
        assert config.personal_token == "ghp_abc"

    def test_from_env_github_app(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_APP_ID", "123")
        monkeypatch.setenv("GITHUB_PRIVATE_KEY", "secret-key")
        monkeypatch.setenv("GITHUB_INSTALLATION_ID", "456")
        config = AuthConfig.from_env()
        assert config.auth_type == AuthType.GITHUB_APP
        assert config.app_id == "123"
        assert config.private_key == "secret-key"

    def test_from_env_github_app_with_key_path(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("file-key-content")
            key_path = f.name
        monkeypatch.setenv("GITHUB_APP_ID", "123")
        monkeypatch.setenv("GITHUB_PRIVATE_KEY_PATH", key_path)
        monkeypatch.delenv("GITHUB_PRIVATE_KEY", raising=False)
        config = AuthConfig.from_env()
        assert config.auth_type == AuthType.GITHUB_APP
        assert config.private_key == "file-key-content"
        os.unlink(key_path)

    def test_from_user_token(self):
        config = AuthConfig.from_user_token("ghp_user_token")
        assert config.auth_type == AuthType.PAT
        assert config.personal_token == "ghp_user_token"

    def test_from_oauth_code(self):
        config = AuthConfig.from_oauth_code("code123", "client_id", "client_secret")
        assert config.auth_type == AuthType.OAUTH
        assert config.authorization_code == "code123"
        assert config.client_id == "client_id"
        assert config.client_secret == "client_secret"

    def test_private_key_path_loading(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("loaded-key")
            key_path = f.name
        config = AuthConfig(
            auth_type=AuthType.GITHUB_APP,
            app_id="1",
            private_key_path=key_path,
        )
        assert config.private_key == "loaded-key"
        os.unlink(key_path)

    def test_private_key_repr_hidden(self):
        config = AuthConfig(
            auth_type=AuthType.GITHUB_APP,
            app_id="1",
            private_key="secret-value",
        )
        rep = repr(config)
        assert "secret-value" not in rep
        assert "private_key" in rep

    def test_personal_token_repr_hidden(self):
        config = AuthConfig(
            auth_type=AuthType.PAT,
            personal_token="ghp_supersecret",
        )
        rep = repr(config)
        assert "ghp_supersecret" not in rep


class TestGitHubAuth:
    @pytest.mark.asyncio
    async def test_authenticate_pat(self):
        config = AuthConfig(auth_type=AuthType.PAT, personal_token="ghp_test123")
        auth = GitHubAuth(config)
        token = await auth.authenticate()
        assert token == "ghp_test123"

    @pytest.mark.asyncio
    async def test_authenticate_unknown(self):
        config = AuthConfig(auth_type=None)  # type: ignore
        auth = GitHubAuth(config)
        with pytest.raises(ValueError, match="Unknown auth type"):
            await auth.authenticate()

    @pytest.mark.asyncio
    async def test_authenticate_oauth_no_code(self):
        config = AuthConfig(
            auth_type=AuthType.OAUTH,
            client_id="cid",
            client_secret="cs",
        )
        auth = GitHubAuth(config)
        with pytest.raises(ValueError, match="authorization_code"):
            await auth.authenticate()

    @pytest.mark.asyncio
    async def test_authenticate_github_app_no_key(self):
        config = AuthConfig(
            auth_type=AuthType.GITHUB_APP,
            app_id="123",
            installation_id="456",
        )
        auth = GitHubAuth(config)
        with pytest.raises(ValueError, match="private_key"):
            await auth.authenticate()

    @pytest.mark.asyncio
    async def test_close(self):
        config = AuthConfig(auth_type=AuthType.PAT, personal_token="test")
        auth = GitHubAuth(config)
        await auth.close()
