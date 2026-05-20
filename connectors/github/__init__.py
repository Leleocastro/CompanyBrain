# GitHub connector package (MVP scaffolding)
from .auth import GitHubAuth
from .client import GitHubClient
from .normalizer import normalize_event
from .ingestor import ingest_repo, ingest_all
from .webhooks import verify_signature
