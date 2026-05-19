import pytest

from ingestao.github_connector.auth import AuthConfig, AuthType, GitHubAuth


class TestAuthConfig:
    def test_from_env_missing(self, monkeypatch):
        for k in ["GITHUB_TOKEN", "GITHUB_APP_ID", "GITHUB_CLIENT_ID"]:
            monkeypatch.delenv(k, raising=False)
        config = AuthConfig.from_env()
        assert config.auth_type == AuthType.OAUTH
        assert config.client_id is None


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
