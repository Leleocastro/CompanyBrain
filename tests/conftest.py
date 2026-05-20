"""Shared test fixtures."""

import os
import pytest


@pytest.fixture(autouse=True)
def clear_gdrive_env():
    """Remove env vars that affect auth before each test."""
    old = {
        k: os.environ.pop(k, None)
        for k in ("GDRIVE_TEST_MODE", "GDRIVE_OAUTH_TOKEN", "GDRIVE_SA_KEYFILE")
    }
    yield
    for k, v in old.items():
        if v is not None:
            os.environ[k] = v


@pytest.fixture
def mock_mode():
    os.environ["GDRIVE_TEST_MODE"] = "mock"
    yield
