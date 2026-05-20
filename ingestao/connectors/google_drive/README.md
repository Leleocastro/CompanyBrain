# Google Drive Connector

Connector for ingesting documents from Google Drive into CompanyBrain.

## Authentication

Two modes:

### 1. OAuth (per-user, recommended)

Each user authorizes their own Drive. Set the env var:

    GDRIVE_OAUTH_TOKEN=<JSON-serialized google.oauth2.credentials.Credentials>

### 2. Service Account (domain-wide delegation)

    export GDRIVE_SA_KEYFILE=/path/to/service-account-key.json

### 3. Mock (local testing, no real credentials)

    export GDRIVE_TEST_MODE=mock

## Usage

```python
from ingestao.connectors import get_connector

conn = get_connector("google_drive")
conn.authenticate()

# List files
files, next_token = conn.list_files(query="name contains 'report'")

# Download a file by ID
raw_bytes = conn.download(file_id)

# Full ingest pipeline
doc = conn.ingest(file_id)  # -> Document with metadata, sha256, PII redacted
```

## Running Tests

```bash
pip install -r requirements.txt
GDRIVE_TEST_MODE=mock pytest tests/ -v
# or
GDRIVE_TEST_MODE=mock python run_gdrive_tests.py
```

## Dependencies

- `google-api-python-client`
- `google-auth`
- `pytest` (dev)
