#!/usr/bin/env python3
"""CLI smoke test for Slack connector scaffolding.

Commands:
  list-channels  -> prints channels (requires SLACK_BOT_TOKEN)
  noop           -> prints a message (safe in CI)
"""
import argparse
import os

from .channels import list_channels


def cli():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["list-channels", "noop"], nargs=1)
    args = p.parse_args()
    cmd = args.command[0]

    if cmd == "noop":
        print("Slack connector scaffold present. Set SLACK_BOT_TOKEN to run real smoke tests.")
        return 0

    if cmd == "list-channels":
        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            print("SLACK_BOT_TOKEN not set — skipping real API call.")
            return 0
        for ch in list_channels():
            print(ch)
        return 0

if __name__ == "__main__":
    raise SystemExit(cli())
