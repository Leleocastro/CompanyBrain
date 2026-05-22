from ingestao.connectors.gmail.auth import GmailAuth, GOOGLE_AUTH_URL


class TestGmailAuth:
    def test_mock_mode_no_creds(self):
        auth = GmailAuth()
        assert auth._is_mock is True

    def test_mock_mode_with_creds(self):
        auth = GmailAuth(client_id="real_id", client_secret="real_secret")
        assert auth._is_mock is False

    def test_get_authorize_url(self):
        auth = GmailAuth(client_id="my_client")
        url = auth.get_authorize_url(state="abc123")
        assert url.startswith(GOOGLE_AUTH_URL)
        assert "client_id=my_client" in url
        assert "state=abc123" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url

    def test_get_authorize_url_default_scopes(self):
        auth = GmailAuth()
        url = auth.get_authorize_url()
        assert "gmail.readonly" in url

    def test_exchange_code_mock(self):
        auth = GmailAuth()
        tokens = auth.exchange_code("auth_code_xyz")
        assert tokens["access_token"] == "mock_access_token"
        assert tokens["refresh_token"] == "mock_refresh_token"
        assert "expires_in" in tokens

    def test_refresh_token_mock(self):
        auth = GmailAuth()
        result = auth.refresh_token("refresh_xyz")
        assert result["access_token"] == "mock_refreshed_token"
        assert "expires_in" in result
        assert "refresh_token" not in result

    def test_scope_str(self):
        auth = GmailAuth(scopes=["scope_a", "scope_b"])
        assert auth._scope_str == "scope_a scope_b"
