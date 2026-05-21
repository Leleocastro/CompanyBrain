import os
from ingestao.connectors.gmail.config import GmailConfig, get_config


class TestGmailConfig:
    def test_default_config(self):
        cfg = GmailConfig()
        assert cfg.client_id is None
        assert cfg.client_secret is None
        assert cfg.redirect_uri == "http://localhost:8000/oauth2callback"
        assert "gmail.readonly" in cfg.scopes[0]
        assert cfg.max_results == 20

    def test_from_env_populates_fields(self):
        os.environ["GMAIL_CLIENT_ID"] = "test_id_123"
        os.environ["GMAIL_CLIENT_SECRET"] = "test_secret_456"
        try:
            cfg = GmailConfig.from_env()
            assert cfg.client_id == "test_id_123"
            assert cfg.client_secret == "test_secret_456"
        finally:
            del os.environ["GMAIL_CLIENT_ID"]
            del os.environ["GMAIL_CLIENT_SECRET"]

    def test_get_config_returns_dict(self):
        cfg = get_config()
        assert isinstance(cfg, dict)
        assert "GMAIL_CLIENT_ID" in cfg
        assert "GMAIL_CLIENT_SECRET" in cfg
        assert "GMAIL_OAUTH_REDIRECT" in cfg
        assert "GMAIL_SCOPES" in cfg
        assert "GMAIL_MAX_RESULTS" in cfg

    def test_custom_max_results(self):
        os.environ["GMAIL_MAX_RESULTS"] = "50"
        try:
            cfg = GmailConfig.from_env()
            assert cfg.max_results == 50
        finally:
            del os.environ["GMAIL_MAX_RESULTS"]
