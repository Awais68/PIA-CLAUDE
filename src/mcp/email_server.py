"""Email MCP Server — provides email tools to Claude Code.

Silver Tier Requirement: S5 (One working MCP server for external action)

Tools:
    - send_email: Draft an email and route through HITL approval
    - search_emails: Search inbox by query
    - list_recent_emails: List N most recent emails

SAFETY: send_email NEVER sends directly. It creates an approval file in
/Pending_Approval/. The email is sent only after human moves file to /Approved/.

Setup:
    1. Gmail API credentials must be set up first (see gmail_watcher.py)
    2. Configure in .claude/mcp.json
    3. Verify: claude mcp list
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Paths — relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"
GMAIL_TOKEN = PROJECT_ROOT / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

mcp = FastMCP("zoya-email")


def _get_gmail_service():
    """Build authenticated Gmail service."""
    if not GMAIL_TOKEN.exists():
        raise RuntimeError(
            "Gmail not authenticated. Run: uv run python scripts/setup_gmail_auth.py"
        )
    creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), SCOPES)
    return build("gmail", "v1", credentials=creds)


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Draft an email and route it through HITL approval.

    Does NOT send immediately. Creates an approval request file
    in /Pending_Approval/. The email is sent only after human approval.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text.

    Returns:
        Status message confirming draft was created.
    """
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_subject = "".join(c if c.isalnum() or c in "_-" else "_" for c in subject)[:40]

    approval_file = PENDING_APPROVAL / f"SEND_EMAIL_{timestamp}_{safe_subject}.md"
    approval_file.write_text(
        f"---\n"
        f"type: email_send\n"
        f"action: send_email\n"
        f"status: pending_approval\n"
        f"to: {to}\n"
        f"subject: {subject}\n"
        f"created: {now.isoformat()}\n"
        f"source: mcp_email_server\n"
        f"approval_required: true\n"
        f"approval_reason: Outbound email requires human approval\n"
        f"---\n\n"
        f"## Email Draft\n\n"
        f"**To:** {to}\n"
        f"**Subject:** {subject}\n\n"
        f"{body}\n\n"
        f"---\n\n"
        f"## To Approve\n"
        f"Move this file to /Approved/ in Obsidian.\n\n"
        f"## To Reject\n"
        f"Move this file to /Rejected/ in Obsidian.\n",
        encoding="utf-8",
    )
    return f"Email draft created and routed for approval: {approval_file.name}"


@mcp.tool()
def search_emails(query: str, max_results: int = 5) -> str:
    """Search Gmail inbox and return matching emails.

    Args:
        query: Gmail search query (e.g., 'from:client@example.com subject:invoice').
        max_results: Maximum number of results to return (default: 5).

    Returns:
        Formatted markdown list of matching emails.
    """
    service = _get_gmail_service()
    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    messages = results.get("messages", [])
    if not messages:
        return "No emails found matching query."

    output_lines = [f"Found {len(messages)} email(s):\n"]
    for msg_summary in messages[:max_results]:
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=msg_summary["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
            .execute()
        )
        headers = {
            h["name"]: h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }
        output_lines.append(
            f"- **{headers.get('Subject', 'No Subject')}** "
            f"from {headers.get('From', 'Unknown')} "
            f"({headers.get('Date', 'Unknown date')})"
        )

    return "\n".join(output_lines)


@mcp.tool()
def list_recent_emails(count: int = 10) -> str:
    """List the N most recent emails in the inbox.

    Args:
        count: Number of recent emails to list (default: 10).

    Returns:
        Formatted markdown list of recent emails.
    """
    return search_emails(query="in:inbox", max_results=count)


def main():
    """Run the MCP server via stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
