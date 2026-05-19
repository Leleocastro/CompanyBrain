from .auth import AuthConfig, AuthType, GitHubAuth
from .client import GitHubClient
from .ingestor import GitHubIngestor, IngestResult
from .normalizer import Document, normalize

__all__ = [
    "GitHubAuth",
    "AuthConfig",
    "AuthType",
    "GitHubClient",
    "GitHubIngestor",
    "IngestResult",
    "Document",
    "normalize",
]
