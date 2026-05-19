from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

import httpx

GITHUB_API_BASE = "https://api.github.com"


@dataclass
class Repository:
    id: int
    name: str
    full_name: str
    description: Optional[str]
    default_branch: str
    url: str
    language: Optional[str]


@dataclass
class Commit:
    sha: str
    author_name: Optional[str]
    author_email: Optional[str]
    author_date: Optional[str]
    message: str
    url: str
    repo_full_name: str


@dataclass
class PullRequest:
    number: int
    title: str
    body: Optional[str]
    author: Optional[str]
    created_at: str
    updated_at: str
    state: str
    url: str
    repo_full_name: str


@dataclass
class Issue:
    number: int
    title: str
    body: Optional[str]
    author: Optional[str]
    created_at: str
    updated_at: str
    state: str
    labels: list[str] = field(default_factory=list)
    url: str = ""
    repo_full_name: str = ""


class GitHubClient:
    def __init__(self, token: str) -> None:
        self.token = token
        self._client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "companybrain-ingestion/1.0",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def list_repositories(self) -> list[Repository]:
        repos: list[Repository] = []
        page = 1
        while True:
            resp = await self._client.get(
                "/user/repos",
                params={
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "type": "all",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            for item in data:
                repos.append(
                    Repository(
                        id=item["id"],
                        name=item["name"],
                        full_name=item["full_name"],
                        description=item.get("description"),
                        default_branch=item["default_branch"],
                        url=item["html_url"],
                        language=item.get("language"),
                    )
                )
            page += 1
            if len(data) < 100:
                break
        return repos

    async def get_repository(self, full_name: str) -> Repository:
        resp = await self._client.get(f"/repos/{full_name}")
        resp.raise_for_status()
        item = resp.json()
        return Repository(
            id=item["id"],
            name=item["name"],
            full_name=item["full_name"],
            description=item.get("description"),
            default_branch=item["default_branch"],
            url=item["html_url"],
            language=item.get("language"),
        )

    async def list_commits(
        self,
        full_name: str,
        branch: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> list[Commit]:
        params: dict[str, Any] = {"per_page": 100}
        if branch:
            params["sha"] = branch
        if since:
            params["since"] = since.isoformat()

        commits: list[Commit] = []
        page = 1
        while True:
            params["page"] = page
            resp = await self._client.get(f"/repos/{full_name}/commits", params=params)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            for item in data:
                author = item.get("commit", {}).get("author", {}) or {}
                commits.append(
                    Commit(
                        sha=item["sha"],
                        author_name=author.get("name"),
                        author_email=author.get("email"),
                        author_date=author.get("date"),
                        message=item["commit"]["message"],
                        url=item["html_url"],
                        repo_full_name=full_name,
                    )
                )
            page += 1
            if len(data) < 100:
                break
        return commits

    async def list_pull_requests(
        self, full_name: str, state: str = "all"
    ) -> list[PullRequest]:
        prs: list[PullRequest] = []
        page = 1
        while True:
            resp = await self._client.get(
                f"/repos/{full_name}/pulls",
                params={"per_page": 100, "page": page, "state": state},
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            for item in data:
                prs.append(
                    PullRequest(
                        number=item["number"],
                        title=item["title"],
                        body=item.get("body"),
                        author=item["user"]["login"] if item.get("user") else None,
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                        state=item["state"],
                        url=item["html_url"],
                        repo_full_name=full_name,
                    )
                )
            page += 1
            if len(data) < 100:
                break
        return prs

    async def list_issues(self, full_name: str, state: str = "all") -> list[Issue]:
        issues: list[Issue] = []
        page = 1
        while True:
            resp = await self._client.get(
                f"/repos/{full_name}/issues",
                params={"per_page": 100, "page": page, "state": state},
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            for item in data:
                if item.get("pull_request"):
                    continue
                issues.append(
                    Issue(
                        number=item["number"],
                        title=item["title"],
                        body=item.get("body"),
                        author=item["user"]["login"] if item.get("user") else None,
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                        state=item["state"],
                        labels=[lb["name"] for lb in item.get("labels", [])],
                        url=item["html_url"],
                        repo_full_name=full_name,
                    )
                )
            page += 1
            if len(data) < 100:
                break
        return issues
