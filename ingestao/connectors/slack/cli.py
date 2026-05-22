import argparse
import sys
import traceback

from ingestao.connectors.slack.client import SlackClient
from ingestao.connectors.slack.channels import list_channels
from ingestao.connectors.slack.threads import fetch_channel_history, fetch_thread
from ingestao.connectors.slack.normalize import normalize_message


def cmd_list_channels(args):
    try:
        client = SlackClient()
        channels = list_channels(client, limit=args.limit)
        print(f"Found {len(channels)} public channels:")
        for ch in channels:
            print(
                f"  {ch['id']}  {ch['name']}  (members: {ch.get('num_members', '?')})"
            )
        return 0
    except Exception as e:
        print(f"Error listing channels: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1


def cmd_fetch_history(args):
    try:
        client = SlackClient()
        messages = fetch_channel_history(client, args.channel, limit=args.limit)
        print(f"Fetched {len(messages)} messages from {args.channel}:")
        for msg in messages:
            doc = normalize_message(msg, args.channel)
            print(f"  [{doc.timestamp}] {doc.author}: {doc.text_excerpt[:120]}")
        return 0
    except Exception as e:
        print(f"Error fetching history: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1


def cmd_fetch_thread(args):
    try:
        client = SlackClient()
        messages = fetch_thread(client, args.channel, args.thread_ts)
        print(f"Fetched {len(messages)} messages in thread {args.thread_ts}:")
        for msg in messages:
            doc = normalize_message(msg, args.channel)
            print(f"  [{doc.timestamp}] {doc.author}: {doc.text_excerpt[:120]}")
        return 0
    except Exception as e:
        print(f"Error fetching thread: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(prog="slack-connector")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list-channels", help="List public channels")
    p_list.add_argument("--limit", type=int, default=200)

    p_history = sub.add_parser("fetch-history", help="Fetch channel history")
    p_history.add_argument("channel")
    p_history.add_argument("--limit", type=int, default=50)

    p_thread = sub.add_parser("fetch-thread", help="Fetch thread replies")
    p_thread.add_argument("channel")
    p_thread.add_argument("thread_ts")

    args = parser.parse_args()
    if args.command == "list-channels":
        return cmd_list_channels(args)
    elif args.command == "fetch-history":
        return cmd_fetch_history(args)
    elif args.command == "fetch-thread":
        return cmd_fetch_thread(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
