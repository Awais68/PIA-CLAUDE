#!/usr/bin/env python3
"""Gmail OAuth2 setup helper for Zoya.

Usage:
    uv run python scripts/setup_gmail_auth.py

Prerequisites:
    1. Go to https://console.cloud.google.com
    2. Create or select a project
    3. Enable the Gmail API (APIs & Services → Library → Gmail API)
    4. Configure OAuth consent screen (External, add your email as test user)
    5. Create OAuth2 Desktop credentials
    6. Download the JSON → save as credentials.json in the project root

This script:
    - Reads credentials.json from project root
    - Opens a browser for Google consent
    - Saves the resulting token to token.json
    - Verifies the connection by listing recent emails
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def main() -> None:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("Missing Google dependencies. Install them with:")
        print("  uv add google-api-python-client google-auth-oauthlib google-auth-httplib2")
        sys.exit(1)

    print("=== Zoya Gmail Authentication Setup ===\n")

    # Step 1: Check credentials.json
    if not GMAIL_CREDENTIALS_FILE.exists():
        print(f"ERROR: credentials.json not found at {GMAIL_CREDENTIALS_FILE}")
        print("\nTo fix this:")
        print("  1. Go to https://console.cloud.google.com")
        print("  2. Create OAuth2 Desktop credentials")
        print("  3. Download the JSON file")
        print(f"  4. Save it as: {GMAIL_CREDENTIALS_FILE}")
        sys.exit(1)

    print(f"Found credentials.json at {GMAIL_CREDENTIALS_FILE}")

    # Step 2: Authenticate
    creds = None
    if GMAIL_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_FILE), SCOPES)
        if creds and creds.valid:
            print(f"Existing token is valid: {GMAIL_TOKEN_FILE}")
        elif creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
            GMAIL_TOKEN_FILE.write_text(creds.to_json())
            print("Token refreshed successfully.")

    if not creds or not creds.valid:
        print("\nOpening browser for Google consent...")
        print("(If no browser opens, copy the URL from the terminal)\n")
        flow = InstalledAppFlow.from_client_secrets_file(
            str(GMAIL_CREDENTIALS_FILE), SCOPES
        )
        creds = flow.run_local_server(port=0)
        GMAIL_TOKEN_FILE.write_text(creds.to_json())
        print(f"\nToken saved to: {GMAIL_TOKEN_FILE}")

    # Step 3: Verify connection
    print("\nVerifying Gmail connection...")
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    email = profile.get("emailAddress", "unknown")
    total = profile.get("messagesTotal", 0)
    print(f"  Connected as: {email}")
    print(f"  Total messages: {total}")

    # Show recent unread count
    results = service.users().messages().list(
        userId="me", q="is:unread", maxResults=5
    ).execute()
    unread = results.get("resultSizeEstimate", 0)
    print(f"  Unread messages: {unread}")

    print("\n=== Setup complete! ===")
    print("You can now start the Gmail watcher:")
    print("  uv run zoya-gmail")


if __name__ == "__main__":
    main()
