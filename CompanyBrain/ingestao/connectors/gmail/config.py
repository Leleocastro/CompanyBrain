"""Configuration helpers for Gmail connector.

Keep configuration minimal for the scaffold: environment-driven settings.
"""
import os
from typing import Optional


def get_config():
    return {
        "GMAIL_CLIENT_ID": os.environ.get("GMAIL_CLIENT_ID"),
        "GMAIL_CLIENT_SECRET": os.environ.get("GMAIL_CLIENT_SECRET"),
        "GMAIL_OAUTH_REDIRECT": os.environ.get("GMAIL_OAUTH_REDIRECT", "http://localhost:8000/oauth2callback"),
    }


if __name__ == "__main__":
    print(get_config())
