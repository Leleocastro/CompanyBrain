"""Minimal GitHub API client scaffolding for the connector MVP.
This file intentionally avoids network calls to keep unit tests fast.
Real implementation should use `requests` or `httpx` and implement pagination.
"""
from typing import List, Dict, Optional

class GitHubClient:
    def __init__(self, auth):
        self.auth = auth

    def list_repos(self, owner: Optional[str] = None) -> List[Dict]:
        """Return a mocked list of repositories. Replace with API calls in production."""
        base = [
            {"full_name": "acme/example", "private": False},
            {"full_name": "acme/internal", "private": True},
        ]
        if owner:
            # filter to simulate owner-specific listing
            return [r for r in base if r["full_name"].startswith(owner + "/")]
        return base

    def list_commits(self, repo_full_name: str, per_page: int = 30):
        return [{"sha": "deadbeef", "message": "Initial commit", "author": {"login": "alice"}}]

    def list_prs(self, repo_full_name: str):
        return [{"id": 1, "title": "Add feature", "user": {"login": "bob"}}]

    def list_issues(self, repo_full_name: str):
        return [{"id": 10, "title": "Bug report", "user": {"login": "carol"}}]
