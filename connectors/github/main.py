"""CLI entrypoints for the GitHub connector (MVP).
This lightweight CLI is useful for manual tests and CI smoke checks.
"""
import argparse
from .auth import GitHubAuth
from .ingestor import ingest_repo, ingest_all


def main(argv=None):
    parser = argparse.ArgumentParser(prog="github-connector")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list-repos")
    p_list.add_argument("--owner", help="Filter by owner (optional)")

    p_ingest = sub.add_parser("ingest-repo")
    p_ingest.add_argument("repo", help="full repo name e.g. owner/name")
    p_ingest.add_argument("--pat", help="Personal Access Token for tests")

    p_all = sub.add_parser("ingest-all")
    p_all.add_argument("--pat", help="Personal Access Token for tests")

    args = parser.parse_args(argv)
    if args.cmd == "list-repos":
        auth = GitHubAuth.from_pat("dummy")
        from .client import GitHubClient
        client = GitHubClient(auth)
        print(client.list_repos(owner=args.owner))
    elif args.cmd == "ingest-repo":
        auth = GitHubAuth.from_pat(args.pat or "dummy")
        docs = ingest_repo(auth, args.repo)
        print(f"Produced {len(docs)} documents")
    elif args.cmd == "ingest-all":
        auth = GitHubAuth.from_pat(args.pat or "dummy")
        docs = ingest_all(auth)
        print(f"Produced {len(docs)} documents")


if __name__ == "__main__":
    main()
