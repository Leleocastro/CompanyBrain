"""Ingestor orchestration for the GitHub connector.
This module wires the client + normalizer and exposes simple entrypoints used by
CLI and higher-level integration tests.
"""
from .client import GitHubClient
from .normalizer import normalize_event
from typing import List, Dict, Any


def ingest_repo(auth, repo_full_name: str) -> List[Dict[str, Any]]:
    client = GitHubClient(auth)
    commits = client.list_commits(repo_full_name)
    prs = client.list_prs(repo_full_name)
    issues = client.list_issues(repo_full_name)

    docs = []
    for c in commits:
        payload = {**c, "full_name": repo_full_name}
        docs.append(normalize_event("github:commit", payload))
    for p in prs:
        payload = {**p, "full_name": repo_full_name}
        docs.append(normalize_event("github:pr", payload))
    for i in issues:
        payload = {**i, "full_name": repo_full_name}
        docs.append(normalize_event("github:issue", payload))
    return docs


def ingest_all(auth) -> List[Dict[str, Any]]:
    client = GitHubClient(auth)
    repos = client.list_repos()
    all_docs = []
    for r in repos:
        all_docs.extend(ingest_repo(auth, r["full_name"]))
    return all_docs
