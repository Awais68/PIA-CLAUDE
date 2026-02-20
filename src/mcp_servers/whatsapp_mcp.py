"""WhatsApp MCP Server — WhatsApp Business API integration for Zoya.

Provides Claude Code with tools to send WhatsApp messages and read
conversation history via Meta Cloud API.

Tools:
    - send_message: Queue a WhatsApp message for HITL approval
    - get_conversation_history: Read recent messages from the vault
    - list_contacts: List known WhatsApp contacts from /Contacts/
    - send_template: Queue a WhatsApp template message (HITL approval)

SAFETY: send_message and send_template NEVER send directly.
        They create approval files in /Pending_Approval/.

Setup:
    1. Meta Business account with WhatsApp Business API enabled
    2. Get Phone Number ID and Access Token
    3. Set in .env:
       WHATSAPP_ACCESS_TOKEN=your-access-token
       WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id

Dependencies:
    uv add mcp requests

TODO: Implement full Meta Cloud API WhatsApp integration.
      See: https://developers.facebook.com/docs/whatsapp/cloud-api
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    print("[whatsapp_mcp] WARNING: mcp package not installed. Run: uv add mcp")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"
CONTACTS_DIR = VAULT_PATH / "Contacts"
DONE_DIR = VAULT_PATH / "Done"

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
GRAPH_API_VERSION = "v19.0"
WA_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _send_wa_message(to: str, payload: dict) -> dict:
    """POST to Meta Cloud API to send a message.

    TODO: Implement with requests library.
    """
    # import requests
    # url = f"{WA_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    # headers = {
    #     "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    #     "Content-Type": "application/json",
    # }
    # resp = requests.post(url, json={"messaging_product": "whatsapp", "to": to, **payload},
    #                      headers=headers, timeout=10)
    # resp.raise_for_status()
    # return resp.json()
    raise NotImplementedError("TODO: Implement Meta Cloud API POST")


if _MCP_AVAILABLE:
    mcp = FastMCP("whatsapp")

    @mcp.tool()
    def send_message(to: str, message: str, context_ref: str = "") -> str:
        """Queue a WhatsApp text message for human approval.

        Args:
            to: Recipient phone number with country code, e.g. "+447911123456"
            message: Message text to send
            context_ref: Reference to what triggered this message (audit trail)

        Returns:
            Path to the approval file in /Pending_Approval/.

        SAFETY: Creates approval file only — human must move to /Approved/ to send.
        """
        PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        safe_to = "".join(c if c.isalnum() else "_" for c in to)[-12:]
        approval_file = PENDING_APPROVAL / f"WHATSAPP_MSG_{ts}_{safe_to}.md"

        content = (
            f"---\n"
            f"type: whatsapp_outbound\n"
            f"platform: whatsapp\n"
            f"to: {to}\n"
            f"created_at: {now.isoformat()}\n"
            f"approval_required: true\n"
            f"status: pending_approval\n"
            f"context_ref: {context_ref}\n"
            f"phone_number_id: {WHATSAPP_PHONE_NUMBER_ID or 'NOT_SET'}\n"
            f"---\n\n"
            f"## WhatsApp Message Draft\n\n"
            f"**To:** {to}\n"
            f"**Context:** {context_ref or 'N/A'}\n\n"
            f"### Message\n\n"
            f"{message}\n\n"
            f"## Actions\n"
            f"- Move to /Approved/ to send via WhatsApp Business API\n"
            f"- Move to /Rejected/ to discard\n\n"
            f"## TODO After Approval\n"
            f"POST to: {WA_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages\n"
            f"Body: {{messaging_product: whatsapp, to: '{to}', type: text, text: {{body: ...}}}}\n"
        )
        approval_file.write_text(content, encoding="utf-8")
        return json.dumps({"approval_file": str(approval_file), "status": "pending_approval"})

    @mcp.tool()
    def get_conversation_history(phone_number: str = "", limit: int = 20) -> str:
        """Read recent WhatsApp messages from the vault.

        Reads processed WHATSAPP_*.md files from /Done/ and /Needs_Action/
        to reconstruct conversation history without hitting the API.

        Args:
            phone_number: Filter by sender phone number (optional)
            limit: Max messages to return (default 20)

        Returns:
            JSON list of messages sorted by received time (newest first).
        """
        messages = []
        search_dirs = [DONE_DIR, PENDING_APPROVAL]

        for d in search_dirs:
            if not d.exists():
                continue
            for f in sorted(d.glob("WHATSAPP_*.md"), reverse=True)[:limit * 2]:
                try:
                    text = f.read_text(encoding="utf-8")
                    # Quick frontmatter parse
                    from_match = None
                    received_match = None
                    body_lines = []
                    in_body = False
                    for line in text.splitlines():
                        if line.startswith("from: "):
                            from_match = line.split("from: ", 1)[1].strip()
                        elif line.startswith("received: "):
                            received_match = line.split("received: ", 1)[1].strip()
                        elif line == "## WhatsApp Message":
                            in_body = True
                        elif in_body and line.startswith("## "):
                            in_body = False
                        elif in_body and line.strip():
                            body_lines.append(line)

                    if phone_number and from_match and phone_number not in from_match:
                        continue

                    messages.append({
                        "from": from_match,
                        "received": received_match,
                        "body": " ".join(body_lines[:3]),
                        "file": f.name,
                    })
                except Exception:
                    continue

        messages = messages[:limit]
        return json.dumps({"messages": messages, "count": len(messages)})

    @mcp.tool()
    def list_contacts() -> str:
        """List known WhatsApp contacts from /Contacts/ directory.

        Returns:
            JSON list of contacts with phone, name, last_interaction.
        """
        if not CONTACTS_DIR.exists():
            return json.dumps({"contacts": [], "count": 0})

        contacts = []
        for f in sorted(CONTACTS_DIR.glob("CONTACT_*.md"))[:50]:
            try:
                text = f.read_text(encoding="utf-8")
                contact = {"file": f.name}
                for line in text.splitlines():
                    for key in ("phone", "name", "email", "last_seen"):
                        if line.startswith(f"{key}: "):
                            contact[key] = line.split(f"{key}: ", 1)[1].strip()
                contacts.append(contact)
            except Exception:
                continue

        return json.dumps({"contacts": contacts, "count": len(contacts)})

    @mcp.tool()
    def send_template(to: str, template_name: str, language_code: str = "en_US", params: str = "") -> str:
        """Queue a WhatsApp template message for HITL approval.

        Template messages are required for proactive outreach (outside 24h window).

        Args:
            to: Recipient phone number with country code
            template_name: Name of the approved WhatsApp template
            language_code: Template language (default "en_US")
            params: JSON string of template parameter values, e.g. '["John", "Monday"]'

        Returns:
            Path to the approval file in /Pending_Approval/.

        TODO: After approval, implement template POST to Cloud API.
        """
        PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        safe_to = "".join(c if c.isalnum() else "_" for c in to)[-12:]
        approval_file = PENDING_APPROVAL / f"WHATSAPP_TPL_{ts}_{safe_to}.md"

        content = (
            f"---\n"
            f"type: whatsapp_template\n"
            f"platform: whatsapp\n"
            f"to: {to}\n"
            f"template_name: {template_name}\n"
            f"language: {language_code}\n"
            f"created_at: {now.isoformat()}\n"
            f"approval_required: true\n"
            f"status: pending_approval\n"
            f"---\n\n"
            f"## WhatsApp Template Message\n\n"
            f"**To:** {to}\n"
            f"**Template:** `{template_name}` ({language_code})\n"
            f"**Parameters:** {params or 'none'}\n\n"
            f"## Actions\n"
            f"- Move to /Approved/ to send template via WhatsApp Business API\n"
            f"- Move to /Rejected/ to discard\n\n"
            f"## TODO After Approval\n"
            f"POST to: {WA_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/messages\n"
            f"Body: {{type: template, template: {{name: '{template_name}', language: {{code: '{language_code}'}}}}}}\n"
        )
        approval_file.write_text(content, encoding="utf-8")
        return json.dumps({"approval_file": str(approval_file), "status": "pending_approval"})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not _MCP_AVAILABLE:
        print("ERROR: mcp package required. Run: uv add mcp")
        raise SystemExit(1)
    if not WHATSAPP_ACCESS_TOKEN:
        print("WARNING: WHATSAPP_ACCESS_TOKEN not set — running in stub mode")
    print("Starting WhatsApp MCP server...")
    mcp.run()
