from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .auth import AuthConfig, GitHubAuth
from .client import GitHubClient
from .normalizer import Document, normalize

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    repo_full_name: str
    commits: list[Document] = field(default_factory=list)
    pull_requests: list[Document] = field(default_factory=list)
    issues: list[Document] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.commits) + len(self.pull_requests) + len(self.issues)


class GitHubIngestor:
    def __init__(
        self,
        auth_config: Optional[AuthConfig] = None,
        batch_size: int = 100,
        max_concurrent_repos: int = 5,
    ) -> None:
        self.auth_config = auth_config or AuthConfig.from_env()
        self.batch_size = batch_size
        self._client: Optional[GitHubClient] = None
        self._semaphore = asyncio.Semaphore(max_concurrent_repos)

    async def _ensure_client(self) -> GitHubClient:
        if self._client is None:
            auth = GitHubAuth(self.auth_config)
            token = await auth.authenticate()
            self._client = GitHubClient(token)
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.close()

    async def list_repos(self) -> list[str]:
        client = await self._ensure_client()
        repos = await client.list_repositories()
        return [r.full_name for r in repos]

    async def ingest_repo(
        self,
        full_name: str,
        since: Optional[datetime] = None,
    ) -> IngestResult:
        client = await self._ensure_client()
        result = IngestResult(repo_full_name=full_name)

        tasks = [
            self._ingest_commits(client, full_name, result, since),
            self._ingest_pull_requests(client, full_name, result),
            self._ingest_issues(client, full_name, result),
        ]
        await asyncio.gather(*tasks)
        return result

    async def _ingest_commits(
        self,
        client: GitHubClient,
        full_name: str,
        result: IngestResult,
        since: Optional[datetime] = None,
    ) -> None:
        try:
            commits = await client.list_commits(full_name, since=since)
            for c in commits:
                doc = normalize("commit", c, full_name)
                result.commits.append(doc)
            logger.info("Ingested %d commits from %s", len(commits), full_name)
        except Exception as e:
            msg = f"Failed to ingest commits from {full_name}: {e}"
            logger.warning(msg)
            result.errors.append(msg)

    async def _ingest_pull_requests(
        self, client: GitHubClient, full_name: str, result: IngestResult
    ) -> None:
        try:
            prs = await client.list_pull_requests(full_name)
            for pr in prs:
                doc = normalize("pull_request", pr, full_name)
                result.pull_requests.append(doc)
            logger.info("Ingested %d PRs from %s", len(prs), full_name)
        except Exception as e:
            msg = f"Failed to ingest PRs from {full_name}: {e}"
            logger.warning(msg)
            result.errors.append(msg)

    async def _ingest_issues(
        self, client: GitHubClient, full_name: str, result: IngestResult
    ) -> None:
        try:
            issues = await client.list_issues(full_name)
            for issue in issues:
                doc = normalize("issue", issue, full_name)
                result.issues.append(doc)
            logger.info("Ingested %d issues from %s", len(issues), full_name)
        except Exception as e:
            msg = f"Failed to ingest issues from {full_name}: {e}"
            logger.warning(msg)
            result.errors.append(msg)

    async def ingest_all_repos(
        self,
        since: Optional[datetime] = None,
    ) -> list[IngestResult]:
        repos = await self.list_repos()

        async def _ingest_one(repo: str) -> IngestResult:
            async with self._semaphore:
                try:
                    return await self.ingest_repo(repo, since=since)
                except Exception as e:
                    logger.error("Skipping repo %s due to error: %s", repo, e)
                    return IngestResult(repo_full_name=repo, errors=[str(e)])

        return await asyncio.gather(*[_ingest_one(r) for r in repos])
