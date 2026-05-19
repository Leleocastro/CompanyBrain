import pytest

from ingestao.github_connector.client import Commit, Issue, PullRequest
from ingestao.github_connector.normalizer import (
    Document,
    compute_sha256,
    normalize,
)


class TestNormalizer:
    def test_compute_sha256(self):
        h = compute_sha256("hello world")
        assert len(h) == 64
        assert h == compute_sha256("hello world")
        assert h != compute_sha256("hello world!")

    def test_normalize_commit(self):
        c = Commit(
            sha="abc123",
            author_name="Alice",
            author_email="alice@example.com",
            author_date="2026-01-15T10:00:00Z",
            message="Fix login bug",
            url="https://github.com/org/repo/commit/abc123",
            repo_full_name="org/repo",
        )
        doc = normalize("commit", c, "org/repo")
        assert isinstance(doc, Document)
        assert doc.id_origem == "abc123"
        assert doc.source == "github/org/repo"
        assert doc.author == "Alice"
        assert doc.timestamp == "2026-01-15T10:00:00Z"
        assert doc.channel == "commit"
        assert doc.path == "org/repo/commit/abc123"
        assert doc.language is None
        assert "Fix login bug" in doc.excerpt
        assert len(doc.sha256) == 64

    def test_normalize_pull_request(self):
        pr = PullRequest(
            number=42,
            title="Add feature X",
            body="Closes #10",
            author="Bob",
            created_at="2026-02-01T12:00:00Z",
            updated_at="2026-02-02T12:00:00Z",
            state="open",
            url="https://github.com/org/repo/pull/42",
            repo_full_name="org/repo",
        )
        doc = normalize("pull_request", pr, "org/repo")
        assert doc.id_origem == "pr-42"
        assert doc.channel == "pull_request"
        assert doc.author == "Bob"
        assert doc.metadata["state"] == "open"

    def test_normalize_issue(self):
        issue = Issue(
            number=7,
            title="Bug in auth",
            body="Steps to reproduce...",
            author="Charlie",
            created_at="2026-03-01T08:00:00Z",
            updated_at="2026-03-02T08:00:00Z",
            state="open",
            labels=["bug", "auth"],
            url="https://github.com/org/repo/issues/7",
            repo_full_name="org/repo",
        )
        doc = normalize("issue", issue, "org/repo")
        assert doc.id_origem == "issue-7"
        assert doc.channel == "issue"
        assert doc.metadata["labels"] == ["bug", "auth"]

    def test_normalize_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown artifact type"):
            normalize("unknown", None, "org/repo")

    def test_excerpt_truncation(self):
        long_msg = "A" * 1000
        c = Commit(
            sha="abc",
            author_name=None,
            author_email=None,
            author_date=None,
            message=long_msg,
            url="",
            repo_full_name="org/repo",
        )
        doc = normalize("commit", c, "org/repo")
        assert len(doc.excerpt) <= 516
        assert doc.excerpt.endswith("...")

    def test_excerpt_empty(self):
        c = Commit(
            sha="abc",
            author_name=None,
            author_email=None,
            author_date=None,
            message="",
            url="",
            repo_full_name="org/repo",
        )
        doc = normalize("commit", c, "org/repo")
        assert doc.excerpt == ""
