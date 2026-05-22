from __future__ import annotations

import pytest

from ingestao.github_connector.auth import AuthConfig, AuthType
from ingestao.github_connector.ingestor import GitHubIngestor, IngestResult

GITHUB_API_BASE = "https://api.github.com"


@pytest.fixture
def ingestor():
    config = AuthConfig(auth_type=AuthType.PAT, personal_token="ghp_test")
    return GitHubIngestor(auth_config=config, max_concurrent_repos=3)


class TestGitHubIngestor:
    async def test_ingest_repo(self, ingestor, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/commits?per_page=100&page=1",
            json=[
                {
                    "sha": "abc",
                    "commit": {
                        "author": {
                            "name": "Alice",
                            "email": "alice@test.com",
                            "date": "2026-01-01T00:00:00Z",
                        },
                        "message": "fix",
                    },
                    "html_url": "https://github.com/user/repo/commit/abc",
                }
            ],
        )
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/pulls?per_page=100&page=1&state=all",
            json=[
                {
                    "number": 1,
                    "title": "PR1",
                    "body": "",
                    "user": {"login": "Bob"},
                    "created_at": "2026-02-01T00:00:00Z",
                    "updated_at": "2026-02-02T00:00:00Z",
                    "state": "open",
                    "html_url": "https://github.com/user/repo/pull/1",
                }
            ],
        )
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/issues?per_page=100&page=1&state=all",
            json=[
                {
                    "number": 7,
                    "title": "Bug",
                    "body": "desc",
                    "user": {"login": "Charlie"},
                    "created_at": "2026-03-01T00:00:00Z",
                    "updated_at": "2026-03-02T00:00:00Z",
                    "state": "open",
                    "labels": [{"name": "bug"}],
                    "html_url": "https://github.com/user/repo/issues/7",
                }
            ],
        )

        result = await ingestor.ingest_repo("user/repo")
        assert isinstance(result, IngestResult)
        assert result.repo_full_name == "user/repo"
        assert len(result.commits) == 1
        assert len(result.pull_requests) == 1
        assert len(result.issues) == 1
        assert result.total == 3
        assert result.errors == []

    async def test_ingest_repo_partial_failure(self, ingestor, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/commits?per_page=100&page=1",
            status_code=500,
        )
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/pulls?per_page=100&page=1&state=all",
            json=[
                {
                    "number": 1,
                    "title": "PR",
                    "body": "",
                    "user": {"login": "Bob"},
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "state": "open",
                    "html_url": "https://github.com/user/repo/pull/1",
                }
            ],
        )
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/issues?per_page=100&page=1&state=all",
            json=[],
        )

        result = await ingestor.ingest_repo("user/repo")
        assert len(result.commits) == 0
        assert len(result.pull_requests) == 1
        assert len(result.issues) == 0
        assert len(result.errors) == 1
        assert "Failed to ingest commits" in result.errors[0]

    async def test_list_repos(self, ingestor, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/user/repos?per_page=100&page=1&sort=updated&type=all",
            json=[
                {
                    "id": 1,
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "description": None,
                    "default_branch": "main",
                    "html_url": "https://github.com/user/repo1",
                    "language": None,
                },
                {
                    "id": 2,
                    "name": "repo2",
                    "full_name": "user/repo2",
                    "description": "desc",
                    "default_branch": "main",
                    "html_url": "https://github.com/user/repo2",
                    "language": "Python",
                },
            ],
        )

        repos = await ingestor.list_repos()
        assert repos == ["user/repo1", "user/repo2"]

    async def test_ingest_all_repos(self, ingestor, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/user/repos?per_page=100&page=1&sort=updated&type=all",
            json=[
                {
                    "id": 1,
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "description": None,
                    "default_branch": "main",
                    "html_url": "",
                    "language": None,
                },
                {
                    "id": 2,
                    "name": "repo2",
                    "full_name": "user/repo2",
                    "description": None,
                    "default_branch": "main",
                    "html_url": "",
                    "language": None,
                },
            ],
        )
        for repo in ["user/repo1", "user/repo2"]:
            httpx_mock.add_response(
                url=f"{GITHUB_API_BASE}/repos/{repo}/commits?per_page=100&page=1",
                json=[],
            )
            httpx_mock.add_response(
                url=f"{GITHUB_API_BASE}/repos/{repo}/pulls?per_page=100&page=1&state=all",
                json=[],
            )
            httpx_mock.add_response(
                url=f"{GITHUB_API_BASE}/repos/{repo}/issues?per_page=100&page=1&state=all",
                json=[],
            )

        results = await ingestor.ingest_all_repos()
        assert len(results) == 2
        for r in results:
            assert r.total == 0
            assert r.errors == []

    async def test_ingest_all_repos_semaphore(self, ingestor, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/user/repos?per_page=100&page=1&sort=updated&type=all",
            json=[
                {
                    "id": i,
                    "name": f"repo{i}",
                    "full_name": f"user/repo{i}",
                    "description": None,
                    "default_branch": "main",
                    "html_url": "",
                    "language": None,
                }
                for i in range(3)
            ],
        )
        for i in range(3):
            repo = f"user/repo{i}"
            httpx_mock.add_response(
                url=f"{GITHUB_API_BASE}/repos/{repo}/commits?per_page=100&page=1",
                json=[],
            )
            httpx_mock.add_response(
                url=f"{GITHUB_API_BASE}/repos/{repo}/pulls?per_page=100&page=1&state=all",
                json=[],
            )
            httpx_mock.add_response(
                url=f"{GITHUB_API_BASE}/repos/{repo}/issues?per_page=100&page=1&state=all",
                json=[],
            )

        results = await ingestor.ingest_all_repos()
        assert len(results) == 3

    async def test_close(self, ingestor):
        await ingestor.close()
