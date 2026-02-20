"""WhatsApp Watcher — receives messages via Meta Cloud API webhook.

Silver Tier Requirement: S2 (Two or more Watcher scripts)

Flow:
    1. Meta Cloud API sends incoming messages to webhook endpoint
    2. Flask server validates and parses the message
    3. Creates a .md file in /Inbox/ with source: whatsapp frontmatter
    4. Downloads media attachments if present
    5. Existing watcher.py + orchestrator pipeline handles the rest

Setup:
    1. Meta Business account with WhatsApp Business API
    2. Set webhook URL (ngrok for dev): http://<url>/webhook
    3. Set verify token in .env: WHATSAPP_VERIFY_TOKEN
    4. Add to .env: WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID

Dependencies:
    uv add flask requests
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, request, jsonify

from src.config import (
    INBOX,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_VERIFY_TOKEN,
    WHATSAPP_WEBHOOK_PORT,
)
from src.utils import log_action
from src.watchers.base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """Receives WhatsApp messages via Meta Cloud API webhook."""

    name = "whatsapp"

    def __init__(self) -> None:
        super().__init__(poll_interval=1, max_retries=5)
        self._app = Flask(__name__)
        self._server_thread: threading.Thread | None = None
        self._message_queue: list[dict] = []
        self._setup_routes()

    # ------------------------------------------------------------------
    # BaseWatcher interface
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """Start the Flask webhook server in a background thread."""
        INBOX.mkdir(parents=True, exist_ok=True)
        self._server_thread = threading.Thread(
            target=self._run_server, daemon=True
        )
        self._server_thread.start()
        self.logger.info("WhatsApp webhook server started on port %d", WHATSAPP_WEBHOOK_PORT)

    def poll(self) -> int:
        """Process any queued messages. Returns count processed."""
        if not self._message_queue:
            return 0

        count = 0
        while self._message_queue:
            msg = self._message_queue.pop(0)
            try:
                self._process_message(msg)
                count += 1
            except Exception as exc:
                self.logger.error("Failed to process WhatsApp message: %s", exc)

        return count

    def teardown(self) -> None:
        self.logger.info("WhatsApp watcher shutting down")

    # ------------------------------------------------------------------
    # Flask routes
    # ------------------------------------------------------------------

    def _setup_routes(self) -> None:
        @self._app.route("/webhook", methods=["GET"])
        def verify():
            """Meta webhook verification (GET request)."""
            mode = request.args.get("hub.mode")
            token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")

            if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
                self.logger.info("Webhook verified successfully")
                return challenge, 200
            return "Forbidden", 403

        @self._app.route("/webhook", methods=["POST"])
        def webhook():
            """Receive incoming WhatsApp messages."""
            data = request.get_json()
            if not data:
                return jsonify({"status": "no data"}), 400

            # Parse Meta Cloud API webhook payload
            messages = self._extract_messages(data)
            for msg in messages:
                self._message_queue.append(msg)
                self.logger.info("Queued WhatsApp message from %s", msg.get("from", "unknown"))

            return jsonify({"status": "ok"}), 200

        @self._app.route("/health", methods=["GET"])
        def health():
            return jsonify(self.health()), 200

        # Test endpoint for demo purposes
        @self._app.route("/test-message", methods=["POST"])
        def test_message():
            """Simulate an incoming WhatsApp message for testing."""
            data = request.get_json() or {}
            msg = {
                "from": data.get("from", "+1234567890"),
                "body": data.get("body", "Test message from WhatsApp"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "text",
                "media_url": data.get("media_url"),
            }
            self._message_queue.append(msg)
            return jsonify({"status": "queued", "message": msg}), 200

    def _run_server(self) -> None:
        self._app.run(host="0.0.0.0", port=WHATSAPP_WEBHOOK_PORT, debug=False, use_reloader=False)

    # ------------------------------------------------------------------
    # Message parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_messages(data: dict) -> list[dict]:
        """Extract messages from Meta Cloud API webhook payload."""
        messages = []
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    parsed = {
                        "from": msg.get("from", "unknown"),
                        "timestamp": msg.get("timestamp", ""),
                        "type": msg.get("type", "text"),
                        "body": "",
                        "media_id": None,
                        "media_url": None,
                    }

                    # Text messages
                    if msg.get("type") == "text":
                        parsed["body"] = msg.get("text", {}).get("body", "")

                    # Image messages
                    elif msg.get("type") == "image":
                        parsed["media_id"] = msg.get("image", {}).get("id")
                        parsed["body"] = msg.get("image", {}).get("caption", "[Image]")

                    # Document messages
                    elif msg.get("type") == "document":
                        parsed["media_id"] = msg.get("document", {}).get("id")
                        parsed["body"] = msg.get("document", {}).get("filename", "[Document]")

                    # Audio/video
                    elif msg.get("type") in ("audio", "video"):
                        parsed["media_id"] = msg.get(msg["type"], {}).get("id")
                        parsed["body"] = f"[{msg['type'].title()} message]"

                    messages.append(parsed)
        return messages

    # ------------------------------------------------------------------
    # Message processing
    # ------------------------------------------------------------------

    def _process_message(self, msg: dict) -> Path:
        """Create a markdown file in /Inbox/ for a WhatsApp message."""
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        safe_from = "".join(c if c.isalnum() else "_" for c in msg["from"])[-12:]

        filepath = INBOX / f"WHATSAPP_{ts}_{safe_from}.md"

        # Download media if present
        media_section = ""
        if msg.get("media_id") and WHATSAPP_ACCESS_TOKEN:
            media_path = self._download_media(msg["media_id"], ts)
            if media_path:
                media_section = f"\n## Media\n- Attachment: `{media_path.name}`\n"

        content = (
            f"---\n"
            f"type: whatsapp_message\n"
            f"source: whatsapp\n"
            f"from: {msg['from']}\n"
            f"message_type: {msg.get('type', 'text')}\n"
            f"received: {now.isoformat()}\n"
            f"status: pending\n"
            f"priority: medium\n"
            f"---\n\n"
            f"## WhatsApp Message\n\n"
            f"**From:** {msg['from']}\n"
            f"**Type:** {msg.get('type', 'text')}\n"
            f"**Received:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            f"{msg.get('body', '')}\n"
            f"{media_section}\n"
            f"## Suggested Actions\n"
            f"- [ ] Review message content\n"
            f"- [ ] Reply to sender (requires approval)\n"
        )
        filepath.write_text(content, encoding="utf-8")

        log_action("whatsapp_ingested", str(filepath), {"from": msg["from"]}, "success")
        self.logger.info("WhatsApp message saved: %s", filepath.name)
        return filepath

    def _download_media(self, media_id: str, timestamp: str) -> Path | None:
        """Download media attachment from Meta Cloud API."""
        try:
            # Step 1: Get media URL
            url = f"https://graph.facebook.com/v18.0/{media_id}"
            headers = {"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            media_url = resp.json().get("url")

            if not media_url:
                return None

            # Step 2: Download the file
            media_resp = requests.get(media_url, headers=headers, timeout=30)
            media_resp.raise_for_status()

            # Determine extension from content type
            content_type = media_resp.headers.get("Content-Type", "")
            ext_map = {
                "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
                "audio/ogg": ".ogg", "audio/mpeg": ".mp3",
                "video/mp4": ".mp4",
                "application/pdf": ".pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            }
            ext = ext_map.get(content_type, ".bin")

            dest = INBOX / f"WA_MEDIA_{timestamp}_{media_id[:8]}{ext}"
            dest.write_bytes(media_resp.content)
            self.logger.info("Media downloaded: %s", dest.name)
            return dest

        except Exception as exc:
            self.logger.error("Failed to download media %s: %s", media_id, exc)
            return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the WhatsApp watcher."""
    INBOX.mkdir(parents=True, exist_ok=True)
    watcher = WhatsAppWatcher()
    watcher.start()


if __name__ == "__main__":
    main()
