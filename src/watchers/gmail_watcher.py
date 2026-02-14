"""Gmail Watcher - polls Gmail for new emails and creates Inbox files.

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
    3. First run: browser consent flow → generates token.json
    4. Both files must be in .gitignore

Dependencies:
    uv add google-api-python-client google-auth-oauthlib google-auth-httplib2
"""

import time
import base64
from datetime import datetime
from pathlib import Path
from email.utils import parseaddr

# TODO: Uncomment after installing dependencies
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

from src.config import (
    INBOX,
    # TODO: Add these to config.py first:
    # GMAIL_POLL_INTERVAL, GMAIL_CREDENTIALS, GMAIL_TOKEN, GMAIL_LABEL,
    PROJECT_ROOT,
)
from src.utils import setup_logger, log_action

logger = setup_logger("gmail_watcher")

# Gmail API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]

# TODO: Move these to config.py
GMAIL_POLL_INTERVAL = 120  # seconds
GMAIL_CREDENTIALS = PROJECT_ROOT / "credentials.json"
GMAIL_TOKEN = PROJECT_ROOT / "token.json"
GMAIL_LABEL = "INBOX"


def authenticate():
    """Authenticate with Gmail API using OAuth2.

    First run opens a browser for consent. Subsequent runs use stored token.

    Returns:
        Credentials object for Gmail API.

    Raises:
        FileNotFoundError: If credentials.json is missing.
    """
    # TODO: Implement after installing google-auth dependencies
    # creds = None
    #
    # if GMAIL_TOKEN.exists():
    #     creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), SCOPES)
    #
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         if not GMAIL_CREDENTIALS.exists():
    #             raise FileNotFoundError(
    #                 f"credentials.json not found at {GMAIL_CREDENTIALS}. "
    #                 "Download from Google Cloud Console."
    #             )
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             str(GMAIL_CREDENTIALS), SCOPES
    #         )
    #         creds = flow.run_local_server(port=0)
    #
    #     GMAIL_TOKEN.write_text(creds.to_json())
    #     logger.info("Gmail authentication successful, token saved")
    #
    # return creds
    raise NotImplementedError("Install google-auth dependencies first")


def get_service(creds):
    """Build Gmail API service client."""
    # TODO: return build("gmail", "v1", credentials=creds)
    raise NotImplementedError("Install google-api-python-client first")


def fetch_unread_messages(service, max_results: int = 10) -> list[dict]:
    """Fetch unread messages from Gmail inbox.

    Args:
        service: Gmail API service client.
        max_results: Maximum number of messages to fetch.

    Returns:
        List of message summaries with 'id' and 'threadId'.
    """
    # TODO: Implement
    # results = service.users().messages().list(
    #     userId="me",
    #     q="is:unread",
    #     labelIds=[GMAIL_LABEL],
    #     maxResults=max_results,
    # ).execute()
    # return results.get("messages", [])
    raise NotImplementedError


def get_message_detail(service, msg_id: str) -> dict:
    """Fetch full message details including headers, body, and attachments.

    Args:
        service: Gmail API service client.
        msg_id: Gmail message ID.

    Returns:
        Full message dict from Gmail API.
    """
    # TODO: Implement
    # return service.users().messages().get(
    #     userId="me", id=msg_id, format="full"
    # ).execute()
    raise NotImplementedError


def extract_headers(message: dict) -> dict[str, str]:
    """Extract common headers (from, to, subject, date) from a Gmail message.

    Args:
        message: Full message dict from Gmail API.

    Returns:
        Dict with lowercase header names as keys.
    """
    headers = {}
    for header in message.get("payload", {}).get("headers", []):
        name = header["name"].lower()
        if name in ("from", "to", "subject", "date"):
            headers[name] = header["value"]
    return headers


def extract_body(message: dict) -> str:
    """Extract plain text body from a Gmail message.

    Handles three cases:
    1. Simple message (no parts) — decode body.data
    2. Multipart message — find text/plain part
    3. Fallback — use message snippet

    Args:
        message: Full message dict from Gmail API.

    Returns:
        Plain text body string.
    """
    payload = message.get("payload", {})

    # Simple message (no parts)
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode(
            "utf-8", errors="replace"
        )

    # Multipart message — find text/plain
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                "utf-8", errors="replace"
            )

    # Fallback to snippet
    return message.get("snippet", "(No body content)")


def save_attachments(service, message: dict, msg_id: str) -> list[str]:
    """Download email attachments to /Inbox/.

    Args:
        service: Gmail API service client.
        message: Full message dict from Gmail API.
        msg_id: Gmail message ID.

    Returns:
        List of saved attachment file paths.
    """
    saved = []
    payload = message.get("payload", {})

    for part in payload.get("parts", []):
        filename = part.get("filename")
        if not filename:
            continue

        att_id = part.get("body", {}).get("attachmentId")
        if not att_id:
            continue

        # TODO: Uncomment after installing dependencies
        # attachment = service.users().messages().attachments().get(
        #     userId="me", messageId=msg_id, id=att_id
        # ).execute()
        #
        # data = base64.urlsafe_b64decode(attachment["data"])
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        # dest = INBOX / f"GMAIL_{timestamp}_{safe_name}"
        # dest.write_bytes(data)
        # saved.append(str(dest))
        # logger.info(f"Attachment saved: {dest.name}")
        pass

    return saved


def create_email_file(
    headers: dict, body: str, msg_id: str, attachments: list[str]
) -> Path:
    """Create a markdown file in /Inbox/ representing the email.

    Args:
        headers: Extracted email headers.
        body: Plain text email body.
        msg_id: Gmail message ID.
        attachments: List of saved attachment paths.

    Returns:
        Path to the created markdown file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _, from_email = parseaddr(headers.get("from", "Unknown"))
    subject = headers.get("subject", "No Subject")
    safe_subject = "".join(c if c.isalnum() or c in "_-" else "_" for c in subject)[
        :60
    ]

    filepath = INBOX / f"EMAIL_{timestamp}_{safe_subject}.md"

    attachment_list = ""
    if attachments:
        attachment_list = "\n".join(f"- `{Path(a).name}`" for a in attachments)
        attachment_list = f"\n## Attachments\n{attachment_list}\n"

    content = f"""---
type: email
source: gmail
from: {headers.get('from', 'Unknown')}
to: {headers.get('to', 'Unknown')}
subject: {subject}
gmail_id: {msg_id}
received: {datetime.now().isoformat()}
status: pending
priority: medium
---

## Email Content

**From:** {headers.get('from', 'Unknown')}
**Subject:** {subject}
**Date:** {headers.get('date', 'Unknown')}

{body[:3000]}
{attachment_list}
## Suggested Actions
- [ ] Review email content
- [ ] Reply to sender
- [ ] Process any attachments
"""
    filepath.write_text(content)
    logger.info(f"Email file created: {filepath.name}")
    return filepath


def mark_as_read(service, msg_id: str):
    """Remove UNREAD label from a message.

    Args:
        service: Gmail API service client.
        msg_id: Gmail message ID.
    """
    # TODO: Implement
    # service.users().messages().modify(
    #     userId="me", id=msg_id,
    #     body={"removeLabelIds": ["UNREAD"]}
    # ).execute()
    pass


def poll_once(service, processed_ids: set) -> int:
    """Run one polling cycle. Returns count of new emails processed.

    Args:
        service: Gmail API service client.
        processed_ids: Set of already-processed message IDs (mutated in place).

    Returns:
        Number of new emails processed this cycle.
    """
    messages = fetch_unread_messages(service)
    count = 0

    for msg_summary in messages:
        msg_id = msg_summary["id"]
        if msg_id in processed_ids:
            continue

        try:
            message = get_message_detail(service, msg_id)
            headers = extract_headers(message)
            body = extract_body(message)
            attachments = save_attachments(service, message, msg_id)
            create_email_file(headers, body, msg_id, attachments)
            mark_as_read(service, msg_id)

            processed_ids.add(msg_id)
            count += 1

            log_action(
                "email_ingested",
                headers.get("subject", "Unknown"),
                {"from": headers.get("from", ""), "gmail_id": msg_id},
                "success",
            )
            logger.info(f"Processed email: {headers.get('subject', 'No Subject')}")

        except Exception as e:
            logger.error(f"Failed to process email {msg_id}: {e}")
            log_action("email_ingested", msg_id, {}, f"error: {e}")

    return count


def main():
    """Main entry point for Gmail watcher."""
    logger.info("Starting Gmail Watcher")
    logger.info(f"Poll interval: {GMAIL_POLL_INTERVAL}s")

    creds = authenticate()
    service = get_service(creds)
    processed_ids: set[str] = set()

    logger.info("Gmail Watcher running. Press Ctrl+C to stop.")

    try:
        while True:
            try:
                count = poll_once(service, processed_ids)
                if count > 0:
                    logger.info(f"Ingested {count} new email(s)")
            except Exception as e:
                logger.error(f"Poll cycle error: {e}")

            time.sleep(GMAIL_POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Gmail Watcher stopped by user")


if __name__ == "__main__":
    main()
