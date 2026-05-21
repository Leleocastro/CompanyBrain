from __future__ import annotations

from datetime import datetime

import httpx
import pytest

from ingestao.github_connector.client import (
    GitHubClient,
)

GITHUB_API_BASE = "https://api.github.com"


@pytest.fixture
def client():
    return GitHubClient("ghp_test_token")


class TestGitHubClient:
    async def test_list_repositories(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/user/repos?per_page=100&page=1&sort=updated&type=all",
            json=[
                {
                    "id": 1,
                    "name": "repo1",
                    "full_name": "user/repo1",
                    "description": "Test repo",
                    "default_branch": "main",
                    "html_url": "https://github.com/user/repo1",
                    "language": "Python",
                }
            ],
        )

        repos = await client.list_repositories()
        assert len(repos) == 1
        assert repos[0].full_name == "user/repo1"
        assert repos[0].language == "Python"

    async def test_list_repositories_empty(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/user/repos?per_page=100&page=1&sort=updated&type=all",
            json=[],
        )

        repos = await client.list_repositories()
        assert repos == []

    async def test_list_repositories_pagination(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/user/repos?per_page=100&page=1&sort=updated&type=all",
            json=[
                {
                    "id": i,
                    "name": f"repo{i}",
                    "full_name": f"user/repo{i}",
                    "description": None,
                    "default_branch": "main",
                    "html_url": f"https://github.com/user/repo{i}",
                    "language": None,
                }
                for i in range(100)
            ],
        )
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/user/repos?per_page=100&page=2&sort=updated&type=all",
            json=[
                {
                    "id": 101,
                    "name": "repo101",
                    "full_name": "user/repo101",
                    "description": None,
                    "default_branch": "main",
                    "html_url": "https://github.com/user/repo101",
                    "language": None,
                }
            ],
        )

        repos = await client.list_repositories()
        assert len(repos) == 101

    async def test_get_repository(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo",
            json={
                "id": 1,
                "name": "repo",
                "full_name": "user/repo",
                "description": "A repo",
                "default_branch": "main",
                "html_url": "https://github.com/user/repo",
                "language": "Go",
            },
        )

        repo = await client.get_repository("user/repo")
        assert repo.full_name == "user/repo"
        assert repo.language == "Go"

    async def test_list_commits(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/commits?per_page=100&page=1",
            json=[
                {
                    "sha": "abc123",
                    "commit": {
                        "author": {
                            "name": "Alice",
                            "email": "alice@example.com",
                            "date": "2026-01-01T00:00:00Z",
                        },
                        "message": "Initial commit",
                    },
                    "html_url": "https://github.com/user/repo/commit/abc123",
                }
            ],
        )

        commits = await client.list_commits("user/repo")
        assert len(commits) == 1
        assert commits[0].sha == "abc123"
        assert commits[0].author_name == "Alice"

    async def test_list_commits_with_branch_and_since(self, client, httpx_mock):
        since = datetime(2026, 1, 15)
        httpx_mock.add_response(
            url=(
                f"{GITHUB_API_BASE}/repos/user/repo/commits"
                f"?per_page=100&page=1&sha=feature&since=2026-01-15T00%3A00%3A00"
            ),
            json=[],
        )

        commits = await client.list_commits("user/repo", branch="feature", since=since)
        assert commits == []

    async def test_list_pull_requests(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/pulls?per_page=100&page=1&state=all",
            json=[
                {
                    "number": 42,
                    "title": "Add feature",
                    "body": "Closes #1",
                    "user": {"login": "Bob"},
                    "created_at": "2026-02-01T12:00:00Z",
                    "updated_at": "2026-02-02T12:00:00Z",
                    "state": "open",
                    "html_url": "https://github.com/user/repo/pull/42",
                }
            ],
        )

        prs = await client.list_pull_requests("user/repo")
        assert len(prs) == 1
        assert prs[0].number == 42
        assert prs[0].author == "Bob"

    async def test_list_issues(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/issues?per_page=100&page=1&state=all",
            json=[
                {
                    "number": 7,
                    "title": "Bug",
                    "body": "Details",
                    "user": {"login": "Charlie"},
                    "created_at": "2026-03-01T08:00:00Z",
                    "updated_at": "2026-03-02T08:00:00Z",
                    "state": "open",
                    "labels": [{"name": "bug"}],
                    "html_url": "https://github.com/user/repo/issues/7",
                }
            ],
        )

        issues = await client.list_issues("user/repo")
        assert len(issues) == 1
        assert issues[0].number == 7
        assert issues[0].labels == ["bug"]

    async def test_list_issues_skips_pull_requests(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo/issues?per_page=100&page=1&state=all",
            json=[
                {
                    "number": 1,
                    "title": "PR-like issue",
                    "user": {"login": "bot"},
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "state": "open",
                    "pull_request": {},
                    "html_url": "https://github.com/user/repo/pull/1",
                }
            ],
        )

        issues = await client.list_issues("user/repo")
        assert issues == []

    async def test_close(self, client):
        await client.close()

    async def test_http_error(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/repos/user/repo",
            status_code=404,
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.get_repository("user/repo")

    async def test_list_repositories_api_error(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{GITHUB_API_BASE}/user/repos?per_page=100&page=1&sort=updated&type=all",
            status_code=500,
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.list_repositories()
