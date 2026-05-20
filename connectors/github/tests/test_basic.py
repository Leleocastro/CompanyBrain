import json
from connectors.github.auth import GitHubAuth
from connectors.github.client import GitHubClient
from connectors.github.ingestor import ingest_repo, ingest_all


def test_auth_from_pat():
    a = GitHubAuth.from_pat("secret_pat")
    assert a.token == "secret_pat"
    assert "token" in a.authorization_header()


def test_oauth_exchange_dummy():
    a = GitHubAuth.from_oauth_code("cid123", "s", "codeXYZ")
    assert a.token.startswith("oauth_dummy_")


def test_client_list_repos():
    a = GitHubAuth.from_pat("p")
    c = GitHubClient(a)
    repos = c.list_repos()
    assert isinstance(repos, list)
    assert any("full_name" in r for r in repos)


def test_ingest_repo_docs_shape():
    a = GitHubAuth.from_pat("p")
    docs = ingest_repo(a, "acme/example")
    assert isinstance(docs, list)
    assert docs
    d = docs[0]
    assert "id_origem" in d and "sha256" in d


def test_ingest_all_works():
    a = GitHubAuth.from_pat("p")
    docs = ingest_all(a)
    assert isinstance(docs, list)

