"""
Google Drive Connector

This directory contains a minimal connector skeleton for Google Drive.

Usage (smoke test without real credentials):

1) In your shell, set environment variable to enable mock mode:

   export GDRIVE_TEST_MODE=mock

2) Run the unit tests:

   pytest CompanyBrain/tests/test_google_drive_client.py -q

Notes:
- This is a skeleton. For production use, replace the placeholder authentication
  with google-auth / google-api-python-client code. Implement proper error handling,
  retries, and streaming downloads for large files.

"""
