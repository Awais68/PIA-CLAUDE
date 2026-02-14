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
    2. Install MCP SDK: uv add mcp
    3. Configure in .claude/mcp.json
    4. Verify: claude mcp list

Dependencies:
    uv add mcp google-api-python-client google-auth-oauthlib google-auth-httplib2
"""

import json
import base64
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText

# TODO: Uncomment after installing mcp SDK
# from mcp.server import Server
# from mcp.types import Tool, TextContent

# TODO: Uncomment after installing google-auth
# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build

# Paths — relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"
GMAIL_TOKEN = PROJECT_ROOT / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# TODO: Uncomment after installing mcp SDK
# app = Server("email-mcp")


def _get_gmail_service():
    """Build authenticated Gmail service.

    Raises:
        RuntimeError: If Gmail is not authenticated (no token.json).
    """
    # TODO: Implement after installing dependencies
    # if not GMAIL_TOKEN.exists():
    #     raise RuntimeError("Gmail not authenticated. Run gmail_watcher first.")
    # creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), SCOPES)
    # return build("gmail", "v1", credentials=creds)
    raise NotImplementedError("Install google-api-python-client first")


# TODO: Uncomment and use proper MCP SDK decorator
# @app.tool()
async def send_email(to: str, subject: str, body: str) -> str:
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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_subject = "".join(c if c.isalnum() or c in "_-" else "_" for c in subject)[
        :40
    ]

    approval_file = PENDING_APPROVAL / f"SEND_EMAIL_{timestamp}_{safe_subject}.md"
    approval_file.write_text(f"""---
type: email_send
action: send_email
status: pending_approval
to: {to}
subject: {subject}
created: {datetime.now().isoformat()}
source: mcp_email_server
approval_required: true
approval_reason: Outbound email requires human approval
---

## Email Draft

**To:** {to}
**Subject:** {subject}

{body}

---

## To Approve
Move this file to /Approved/ in Obsidian.

## To Reject
Move this file to /Rejected/ in Obsidian.
""")
    return f"Email draft created and routed for approval: {approval_file.name}"


# TODO: Uncomment and use proper MCP SDK decorator
# @app.tool()
async def search_emails(query: str, max_results: int = 5) -> str:
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


# TODO: Uncomment and use proper MCP SDK decorator
# @app.tool()
async def list_recent_emails(count: int = 10) -> str:
    """List the N most recent emails in the inbox.

    Args:
        count: Number of recent emails to list (default: 10).

    Returns:
        Formatted markdown list of recent emails.
    """
    return await search_emails(query="in:inbox", max_results=count)


def main():
    """Run the MCP server."""
    # TODO: Uncomment after installing mcp SDK
    # import asyncio
    # asyncio.run(app.run())
    raise NotImplementedError("Install mcp SDK first: uv add mcp")


if __name__ == "__main__":
    main()
