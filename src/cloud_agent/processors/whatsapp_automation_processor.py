"""
WhatsApp Automation Processor
Handles WhatsApp messaging and media sending tasks
Integrates with Playwright-based MCP server for local automation
"""

import asyncio
import re
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict

from src.mcp_servers.whatsapp_mcp_playwright import get_whatsapp_playwright_server
from src.utils import setup_logger, log_action

logger = setup_logger("whatsapp_processor")


class WhatsAppAutomationProcessor:
    """Process WhatsApp automation tasks from vault files"""

    def __init__(self):
        """Initialize processor with WhatsApp MCP server"""
        self.mcp_server = get_whatsapp_playwright_server()

    def process_message_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a WhatsApp message task

        Args:
            metadata: Task metadata (from frontmatter)
            content: Message content and recipient

        Returns:
            Result dict with success status
        """
        try:
            contact = self._extract_field(content, "Contact")
            message = self._extract_section(content, "Message Content")

            if not contact or not message:
                return {
                    "success": False,
                    "error": "Contact and message required"
                }

            # Send message
            result = asyncio.run(self.mcp_server.send_message(contact, message))

            if result.get("success"):
                log_action(
                    "whatsapp_message_processed",
                    "whatsapp_processor",
                    {
                        "task_type": "message",
                        "contact": contact,
                        "message_length": len(message),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    result="success"
                )
                return {
                    "success": True,
                    "action": "message_sent",
                    "summary": f"WhatsApp message sent to {contact}",
                    "contact": contact
                }
            else:
                logger.error(f"WhatsApp message failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Message send failed")
                }

        except Exception as e:
            logger.exception(f"Error processing WhatsApp message task: {e}")
            return {"success": False, "error": str(e)}

    def process_media_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a WhatsApp media task (image/video)

        Args:
            metadata: Task metadata
            content: Media path and caption

        Returns:
            Result dict
        """
        try:
            contact = self._extract_field(content, "Contact")
            media_path = self._extract_field(content, "Media Path")
            caption = self._extract_section(content, "Caption")

            if not contact or not media_path:
                return {
                    "success": False,
                    "error": "Contact and media path required"
                }

            # Check if media file exists
            if not os.path.exists(media_path):
                return {
                    "success": False,
                    "error": f"Media file not found: {media_path}"
                }

            # Send media
            result = asyncio.run(self.mcp_server.send_media(contact, media_path, caption))

            if result.get("success"):
                log_action(
                    "whatsapp_media_processed",
                    "whatsapp_processor",
                    {
                        "task_type": "media",
                        "contact": contact,
                        "media_file": os.path.basename(media_path),
                        "has_caption": bool(caption),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    result="success"
                )
                return {
                    "success": True,
                    "action": "media_sent",
                    "summary": f"Media sent to {contact}",
                    "contact": contact,
                    "media": os.path.basename(media_path)
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Failed to send media")
                }

        except Exception as e:
            logger.exception(f"Error processing WhatsApp media task: {e}")
            return {"success": False, "error": str(e)}

    def process_broadcast_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a broadcast task (send to multiple contacts)

        Args:
            metadata: Task metadata
            content: Message and contact list

        Returns:
            Result dict
        """
        try:
            contacts_str = self._extract_field(content, "Contacts")
            message = self._extract_section(content, "Message Content")

            if not contacts_str or not message:
                return {
                    "success": False,
                    "error": "Contacts and message required"
                }

            # Parse contact list (comma-separated)
            contacts = [c.strip() for c in contacts_str.split(",")]

            sent_count = 0
            failed_contacts = []

            for contact in contacts:
                result = asyncio.run(self.mcp_server.send_message(contact, message))
                if result.get("success"):
                    sent_count += 1
                else:
                    failed_contacts.append(contact)

            log_action(
                "whatsapp_broadcast_processed",
                "whatsapp_processor",
                {
                    "task_type": "broadcast",
                    "total_contacts": len(contacts),
                    "sent": sent_count,
                    "failed": len(failed_contacts),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                result="success" if sent_count > 0 else "error"
            )

            if sent_count == len(contacts):
                return {
                    "success": True,
                    "action": "broadcast_sent",
                    "summary": f"Message sent to {sent_count} contacts",
                    "sent_count": sent_count
                }
            else:
                return {
                    "success": sent_count > 0,
                    "summary": f"Sent to {sent_count}/{len(contacts)} contacts",
                    "sent_count": sent_count,
                    "failed_contacts": failed_contacts
                }

        except Exception as e:
            logger.exception(f"Error processing WhatsApp broadcast task: {e}")
            return {"success": False, "error": str(e)}

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section from task content"""
        pattern = rf"## {section_name}\s*\n(.*?)(?=##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_field(self, content: str, field_name: str, default: str = "") -> str:
        """Extract a field from task content"""
        pattern = rf"\*\*{field_name}:\*\*\s*(.+?)(?:\n|$)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return default


def process_whatsapp_task(meta_path: Path) -> bool:
    """
    Main entry point for processing WhatsApp tasks from orchestrator

    Args:
        meta_path: Path to metadata file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read metadata file
        content = meta_path.read_text(encoding="utf-8")

        # Extract frontmatter
        fm_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        metadata = {}
        if fm_match:
            for line in fm_match.group(1).splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    metadata[key.strip()] = value.strip()

        # Extract task content (after frontmatter)
        body_start = fm_match.end() if fm_match else 0
        task_content = content[body_start:].strip()

        # Process based on task type
        processor = WhatsAppAutomationProcessor()
        task_type = metadata.get("task_type", "message").lower()

        if task_type == "message":
            result = processor.process_message_task(metadata, task_content)
        elif task_type == "media":
            result = processor.process_media_task(metadata, task_content)
        elif task_type == "broadcast":
            result = processor.process_broadcast_task(metadata, task_content)
        else:
            result = {"success": False, "error": f"Unknown task type: {task_type}"}

        # Update metadata file with result
        if result.get("success"):
            _update_metadata(meta_path, {
                "status": "done",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "result": "success"
            })
            logger.info(f"✅ WhatsApp task processed: {result.get('summary')}")
            return True
        else:
            _update_metadata(meta_path, {
                "status": "failed",
                "error": result.get("error"),
                "failed_at": datetime.now(timezone.utc).isoformat()
            })
            logger.error(f"❌ WhatsApp task failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.exception(f"Error processing WhatsApp task: {e}")
        return False


def _update_metadata(path: Path, updates: Dict[str, str]) -> None:
    """Update metadata file frontmatter"""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return

    fm_lines = match.group(1).splitlines()
    new_lines = []
    updated_keys = set()

    for line in fm_lines:
        if ":" in line:
            key = line.partition(":")[0].strip()
            if key in updates:
                new_lines.append(f"{key}: {updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Add missing keys
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}: {val}")

    new_fm = "---\n" + "\n".join(new_lines) + "\n---"
    rest = text[match.end():]
    path.write_text(new_fm + rest, encoding="utf-8")
