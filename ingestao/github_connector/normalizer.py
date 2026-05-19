from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Document:
    id_origem: str
    source: str
    author: Optional[str]
    timestamp: Optional[str]
    channel: str
    path: str
    language: Optional[str]
    excerpt: str
    sha256: str
    metadata: dict[str, Any] = field(default_factory=dict)


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _truncate_excerpt(text: Optional[str], max_len: int = 512) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def normalize_commit(commit: Any, repo_full_name: str) -> Document:
    raw = f"{commit.sha}:{commit.message}:{commit.author_name}:{commit.author_date}"
    excerpt = _truncate_excerpt(commit.message)
    return Document(
        id_origem=commit.sha,
        source=f"github/{repo_full_name}",
        author=commit.author_name,
        timestamp=commit.author_date,
        channel="commit",
        path=f"{repo_full_name}/commit/{commit.sha}",
        language=None,
        excerpt=excerpt,
        sha256=compute_sha256(raw),
        metadata={
            "sha": commit.sha,
            "author_email": commit.author_email,
            "url": commit.url,
        },
    )


def normalize_pull_request(pr: Any, repo_full_name: str) -> Document:
    raw = f"pr-{pr.number}:{pr.title}:{pr.body or ''}:{pr.author}:{pr.state}"
    excerpt = _truncate_excerpt(pr.body or pr.title)
    return Document(
        id_origem=f"pr-{pr.number}",
        source=f"github/{repo_full_name}",
        author=pr.author,
        timestamp=pr.created_at,
        channel="pull_request",
        path=f"{repo_full_name}/pull/{pr.number}",
        language=None,
        excerpt=excerpt,
        sha256=compute_sha256(raw),
        metadata={
            "number": pr.number,
            "title": pr.title,
            "state": pr.state,
            "url": pr.url,
        },
    )


def normalize_issue(issue: Any, repo_full_name: str) -> Document:
    body = issue.body or ""
    raw = f"issue-{issue.number}:{issue.title}:{body}:{issue.author}:{issue.state}"
    excerpt = _truncate_excerpt(issue.body or issue.title)
    return Document(
        id_origem=f"issue-{issue.number}",
        source=f"github/{repo_full_name}",
        author=issue.author,
        timestamp=issue.created_at,
        channel="issue",
        path=f"{repo_full_name}/issues/{issue.number}",
        language=None,
        excerpt=excerpt,
        sha256=compute_sha256(raw),
        metadata={
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "labels": issue.labels,
            "url": issue.url,
        },
    )


def normalize(artifact_type: str, artifact: Any, repo_full_name: str) -> Document:
    normalizers = {
        "commit": normalize_commit,
        "pull_request": normalize_pull_request,
        "issue": normalize_issue,
    }
    fn = normalizers.get(artifact_type)
    if not fn:
        raise ValueError(f"Unknown artifact type: {artifact_type}")
    return fn(artifact, repo_full_name)
