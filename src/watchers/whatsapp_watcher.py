"""WhatsApp Watcher — receives messages via Twilio webhook.

Silver Tier Requirement: S2 (Two or more Watcher scripts)

Flow:
    1. Twilio WhatsApp Sandbox sends incoming messages to webhook
    2. Flask server parses the message
    3. Creates a .md file in /Inbox/ with source: whatsapp frontmatter
    4. Existing watcher.py + orchestrator pipeline handles the rest

Setup:
    1. Create Twilio account at https://www.twilio.com
    2. Activate WhatsApp Sandbox (Messaging > Try WhatsApp)
    3. Install ngrok: https://ngrok.com
    4. Run: ngrok http 5001
    5. Set Twilio webhook URL to: http://<your-ngrok-url>/whatsapp
    6. Add to .env:
       TWILIO_ACCOUNT_SID=your_sid
       TWILIO_AUTH_TOKEN=your_token

Dependencies:
    uv add flask twilio
"""

import os
from datetime import datetime
from pathlib import Path

# TODO: Uncomment after installing dependencies
# from flask import Flask, request
# from twilio.twiml.messaging_response import MessagingResponse

from src.config import INBOX, PROJECT_ROOT
from src.utils import setup_logger, log_action

logger = setup_logger("whatsapp_watcher")

# TODO: Uncomment after installing Flask
# app = Flask(__name__)

WEBHOOK_PORT = int(os.getenv("WHATSAPP_PORT", "5001"))


def create_message_file(
    from_number: str, body: str, media_url: str | None = None
) -> Path:
    """Create a markdown file in /Inbox/ for an incoming WhatsApp message.

    Args:
        from_number: Sender's phone number (e.g., "whatsapp:+1234567890").
        body: Message text content.
        media_url: Optional URL of attached media.

    Returns:
        Path to the created markdown file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_from = "".join(c if c.isalnum() else "_" for c in from_number)[-10:]

    filepath = INBOX / f"WHATSAPP_{timestamp}_{safe_from}.md"

    media_section = ""
    if media_url:
        media_section = f"\n## Media\n- Attachment: {media_url}\n"

    filepath.write_text(f"""---
type: whatsapp_message
source: whatsapp
from: {from_number}
received: {datetime.now().isoformat()}
status: pending
priority: medium
---

## WhatsApp Message

**From:** {from_number}
**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{body}
{media_section}
## Suggested Actions
- [ ] Review message content
- [ ] Reply to sender (requires approval)
""")

    logger.info(f"WhatsApp message saved: {filepath.name}")
    log_action("whatsapp_ingested", str(filepath), {"from": from_number}, "success")
    return filepath


# TODO: Uncomment after installing Flask + Twilio
#
# @app.route("/whatsapp", methods=["POST"])
# def whatsapp_webhook():
#     """Handle incoming WhatsApp messages from Twilio.
#
#     Twilio sends POST with form data:
#         - From: sender number (e.g., "whatsapp:+1234567890")
#         - Body: message text
#         - NumMedia: number of media attachments
#         - MediaUrl0: URL of first attachment (if any)
#     """
#     from_number = request.values.get("From", "Unknown")
#     body = request.values.get("Body", "")
#     media_url = request.values.get("MediaUrl0")
#     num_media = int(request.values.get("NumMedia", 0))
#
#     logger.info(f"WhatsApp message from {from_number}: {body[:50]}...")
#
#     create_message_file(from_number, body, media_url if num_media > 0 else None)
#
#     # Acknowledge receipt
#     resp = MessagingResponse()
#     # Uncomment to auto-acknowledge:
#     # resp.message("Received. Zoya is processing your message.")
#     return str(resp)
#
#
# @app.route("/health", methods=["GET"])
# def health():
#     """Health check endpoint."""
#     return {"status": "ok", "service": "whatsapp_watcher"}


def main():
    """Start the WhatsApp webhook server."""
    logger.info(f"WhatsApp Watcher starting on port {WEBHOOK_PORT}")
    logger.info(f"Ensure ngrok is running: ngrok http {WEBHOOK_PORT}")
    # TODO: Uncomment after installing Flask
    # app.run(host="0.0.0.0", port=WEBHOOK_PORT, debug=False)
    raise NotImplementedError("Install flask and twilio dependencies first")


if __name__ == "__main__":
    main()
