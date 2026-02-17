"""Gmail Watcher — polls Gmail for new emails and creates Inbox files.

Silver Tier Requirement: S2 (Two or more Watcher scripts)

Flow:
    1. Authenticate via stored OAuth2 token (first run opens browser)
    2. Poll for unread messages every GMAIL_POLL_INTERVAL seconds
    3. For each new email:
       - Download attachments to /Inbox/
       - Create email summary .md in /Inbox/ with source: gmail frontmatter
       - Mark as read in Gmail
    4. Existing watcher.py + orchestrator pipeline handles the rest

Setup:
    1. Create Google Cloud project + enable Gmail API
    2. Create OAuth2 Desktop credentials → download credentials.json
    3. Run:  uv run python scripts/setup_gmail_auth.py
    4. Both credentials.json and token.json must be in .gitignore

Dependencies:
    uv add google-api-python-client google-auth-oauthlib google-auth-httplib2
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from email.utils import parseaddr
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config import (
    GMAIL_CREDENTIALS_FILE,
    GMAIL_MAX_RESULTS,
    GMAIL_POLL_INTERVAL,
    GMAIL_TOKEN_FILE,
    INBOX,
)
from src.utils import log_action
from src.watchers.base_watcher import BaseWatcher

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailWatcher(BaseWatcher):
    """Polls Gmail for unread emails and ingests them into the vault."""

    name = "gmail"

    def __init__(self) -> None:
        super().__init__(poll_interval=GMAIL_POLL_INTERVAL)
        self._service = None
        self._processed_ids: set[str] = set()

    # ------------------------------------------------------------------
    # BaseWatcher interface
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """Authenticate and build the Gmail API service."""
        creds = self._authenticate()
        self._service = build("gmail", "v1", credentials=creds)
        self.logger.info("Gmail API service initialised")

    def poll(self) -> int:
        """Fetch unread emails and ingest them. Returns count processed."""
        messages = self._fetch_unread()
        count = 0

        for msg_summary in messages:
            msg_id = msg_summary["id"]
            if msg_id in self._processed_ids:
                continue

            try:
                message = self._get_message_detail(msg_id)
                headers = self._extract_headers(message)
                body = self._extract_body(message)
                attachments = self._save_attachments(message, msg_id)
                self._create_email_file(headers, body, msg_id, attachments)
                self._mark_as_read(msg_id)

                self._processed_ids.add(msg_id)
                count += 1

                log_action(
                    "email_ingested",
                    headers.get("subject", "Unknown"),
                    {"from": headers.get("from", ""), "gmail_id": msg_id},
                    "success",
                )
                self.logger.info("Processed email: %s", headers.get("subject", "(no subject)"))

            except Exception as exc:
                self.logger.error("Failed to process email %s: %s", msg_id, exc)
                log_action("email_ingested", msg_id, {}, f"error: {exc}")

        return count

    def teardown(self) -> None:
        self._service = None

    # ------------------------------------------------------------------
    # Gmail helpers
    # ------------------------------------------------------------------

    def _authenticate(self) -> Credentials:
        """OAuth2 authentication — uses stored token or opens browser."""
        creds = None

        if GMAIL_TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_FILE), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not GMAIL_CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"credentials.json not found at {GMAIL_CREDENTIALS_FILE}. "
                        "Download from Google Cloud Console, or run: "
                        "uv run python scripts/setup_gmail_auth.py"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(GMAIL_CREDENTIALS_FILE), SCOPES
                )
                creds = flow.run_local_server(port=0)

            GMAIL_TOKEN_FILE.write_text(creds.to_json())
            self.logger.info("Gmail token saved to %s", GMAIL_TOKEN_FILE)

        return creds

    def _fetch_unread(self) -> list[dict]:
        results = (
            self._service.users()
            .messages()
            .list(userId="me", q="is:unread", labelIds=["INBOX"], maxResults=GMAIL_MAX_RESULTS)
            .execute()
        )
        return results.get("messages", [])

    def _get_message_detail(self, msg_id: str) -> dict:
        return (
            self._service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

    @staticmethod
    def _extract_headers(message: dict) -> dict[str, str]:
        headers: dict[str, str] = {}
        for header in message.get("payload", {}).get("headers", []):
            name = header["name"].lower()
            if name in ("from", "to", "subject", "date"):
                headers[name] = header["value"]
        return headers

    @staticmethod
    def _extract_body(message: dict) -> str:
        payload = message.get("payload", {})

        # Simple message
        if "body" in payload and payload["body"].get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

        # Multipart — find text/plain
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

        return message.get("snippet", "(No body content)")

    def _save_attachments(self, message: dict, msg_id: str) -> list[str]:
        saved: list[str] = []
        payload = message.get("payload", {})

        for part in payload.get("parts", []):
            filename = part.get("filename")
            if not filename:
                continue
            att_id = part.get("body", {}).get("attachmentId")
            if not att_id:
                continue

            attachment = (
                self._service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=msg_id, id=att_id)
                .execute()
            )
            data = base64.urlsafe_b64decode(attachment["data"])
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
            dest = INBOX / f"GMAIL_{ts}_{safe_name}"
            dest.write_bytes(data)
            saved.append(str(dest))
            self.logger.info("Attachment saved: %s", dest.name)

        return saved

    def _create_email_file(
        self, headers: dict, body: str, msg_id: str, attachments: list[str]
    ) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        _, from_email = parseaddr(headers.get("from", "Unknown"))
        subject = headers.get("subject", "No Subject")
        safe_subject = "".join(c if c.isalnum() or c in "_-" else "_" for c in subject)[:60]

        filepath = INBOX / f"EMAIL_{ts}_{safe_subject}.md"

        attachment_section = ""
        if attachments:
            items = "\n".join(f"- `{Path(a).name}`" for a in attachments)
            attachment_section = f"\n## Attachments\n{items}\n"

        content = f"""---
type: email
source: gmail
from: {headers.get('from', 'Unknown')}
to: {headers.get('to', 'Unknown')}
subject: {subject}
gmail_id: {msg_id}
received: {datetime.now(timezone.utc).isoformat()}
status: pending
priority: medium
---

## Email Content

**From:** {headers.get('from', 'Unknown')}
**Subject:** {subject}
**Date:** {headers.get('date', 'Unknown')}

{body[:3000]}
{attachment_section}
## Suggested Actions
- [ ] Review email content
- [ ] Reply to sender
- [ ] Process any attachments
"""
        filepath.write_text(content, encoding="utf-8")
        self.logger.info("Email file created: %s", filepath.name)
        return filepath

    def _mark_as_read(self, msg_id: str) -> None:
        self._service.users().messages().modify(
            userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the Gmail watcher."""
    INBOX.mkdir(parents=True, exist_ok=True)
    watcher = GmailWatcher()
    watcher.start()


if __name__ == "__main__":
    main()
