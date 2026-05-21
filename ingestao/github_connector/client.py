from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

import httpx

GITHUB_API_BASE = "https://api.github.com"
PER_PAGE = 100

T = TypeVar("T")


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
    def __init__(self, token: str, timeout: int = 30) -> None:
        self.token = token
        self._client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "companybrain-ingestion/1.0",
            },
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        parse_item: Callable[[dict], T | None] | None = None,
    ) -> list[T]:
        if params is None:
            params = {}
        params.setdefault("per_page", PER_PAGE)

        items: list[T] = []
        page = 1
        while True:
            params["page"] = page
            resp = await self._client.get(path, params=params)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            if parse_item:
                for item in data:
                    parsed = parse_item(item)
                    if parsed is not None:
                        items.append(parsed)
            else:
                items.extend(data)
            page += 1
            if len(data) < PER_PAGE:
                break
        return items

    async def list_repositories(self) -> list[Repository]:
        def parse(item: dict) -> Repository:
            return Repository(
                id=item["id"],
                name=item["name"],
                full_name=item["full_name"],
                description=item.get("description"),
                default_branch=item["default_branch"],
                url=item["html_url"],
                language=item.get("language"),
            )

        return await self._paginate(
            "/user/repos",
            params={"sort": "updated", "type": "all"},
            parse_item=parse,
        )

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
        params: dict[str, Any] = {}
        if branch:
            params["sha"] = branch
        if since:
            params["since"] = since.isoformat()

        def parse(item: dict) -> Commit:
            author = item.get("commit", {}).get("author", {}) or {}
            return Commit(
                sha=item["sha"],
                author_name=author.get("name"),
                author_email=author.get("email"),
                author_date=author.get("date"),
                message=item["commit"]["message"],
                url=item["html_url"],
                repo_full_name=full_name,
            )

        return await self._paginate(
            f"/repos/{full_name}/commits",
            params=params,
            parse_item=parse,
        )

    async def list_pull_requests(
        self, full_name: str, state: str = "all"
    ) -> list[PullRequest]:
        def parse(item: dict) -> PullRequest:
            return PullRequest(
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

        return await self._paginate(
            f"/repos/{full_name}/pulls",
            params={"state": state},
            parse_item=parse,
        )

    async def list_issues(self, full_name: str, state: str = "all") -> list[Issue]:
        def parse(item: dict) -> Issue | None:
            if "pull_request" in item:
                return None
            return Issue(
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

        items = await self._paginate(
            f"/repos/{full_name}/issues",
            params={"state": state},
            parse_item=parse,
        )
        return [i for i in items if i is not None]
