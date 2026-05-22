from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta

from ingestao.github_connector.auth import AuthConfig
from ingestao.github_connector.ingestor import GitHubIngestor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("github-connector")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GitHub Connector — CompanyBrain ingestion"
    )
    parser.add_argument(
        "action",
        choices=["list-repos", "ingest-repo", "ingest-all"],
        help="Action to perform",
    )
    parser.add_argument("--repo", help="Repository full name (e.g., org/repo)")
    parser.add_argument(
        "--since",
        type=int,
        default=24,
        help="Ingest artifacts since N hours ago (default: 24)",
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (PAT) for end-user auth",
    )
    parser.add_argument(
        "--output",
        choices=["json", "summary"],
        default="summary",
        help="Output format (default: summary)",
    )
    args = parser.parse_args()

    since = datetime.utcnow() - timedelta(hours=args.since)

    async def run() -> None:
        auth_config = AuthConfig.from_user_token(args.token) if args.token else None
        ingestor = GitHubIngestor(auth_config=auth_config)
        try:
            if args.action == "list-repos":
                repos = await ingestor.list_repos()
                if args.output == "json":
                    print(json.dumps(repos, indent=2))
                else:
                    print(f"Found {len(repos)} repositorie(s):")
                    for r in repos:
                        print(f"  - {r}")

            elif args.action == "ingest-repo":
                if not args.repo:
                    print("ERROR: --repo is required for ingest-repo", file=sys.stderr)
                    sys.exit(1)
                result = await ingestor.ingest_repo(args.repo, since=since)
                _print_result(result, args.output)

            elif args.action == "ingest-all":
                results = await ingestor.ingest_all_repos(since=since)
                for r in results:
                    _print_result(r, args.output)
        finally:
            await ingestor.close()

    asyncio.run(run())


def _print_result(result, output: str) -> None:
    if output == "json":
        print(
            json.dumps(
                {
                    "repo": result.repo_full_name,
                    "commits": [d.__dict__ for d in result.commits],
                    "pull_requests": [d.__dict__ for d in result.pull_requests],
                    "issues": [d.__dict__ for d in result.issues],
                    "errors": result.errors,
                    "total": result.total,
                },
                indent=2,
                default=str,
            )
        )
    else:
        print(f"\nRepo: {result.repo_full_name}")
        print(f"  Commits: {len(result.commits)}")
        print(f"  PRs:     {len(result.pull_requests)}")
        print(f"  Issues:  {len(result.issues)}")
        if result.errors:
            print(f"  Errors: {len(result.errors)}")
            for err in result.errors:
                print(f"    - {err}")
        print(f"  Total:   {result.total}")


if __name__ == "__main__":
    main()
