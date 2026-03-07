"""
WhatsApp MCP Server - Playwright-based Implementation
Uses local WhatsApp Web browser automation instead of Cloud API
Ideal for personal automation without WhatsApp Business API setup
"""

import asyncio
import os
from datetime import datetime
from typing import Optional, Dict, List

from src.automations.whatsapp_playwright import WhatsAppPlaywright
from src.playwright_utils import safe_async_run
from src.utils import setup_logger, log_action

logger = setup_logger("whatsapp_playwright")


class WhatsAppMCPPlaywright:
    """WhatsApp MCP Server - Handles browser-based WhatsApp automation"""

    def __init__(self):
        """Initialize WhatsApp Playwright client"""
        self.authenticated = True  # Playwright logs in via QR code
        self.headless = os.getenv("WHATSAPP_HEADLESS", "true").lower() == "true"

    async def send_message(
        self,
        contact_name: str,
        message: str
    ) -> Dict:
        """
        Send WhatsApp message to a contact

        Args:
            contact_name: Name of contact in WhatsApp
            message: Message text to send

        Returns:
            Dict with status
        """
        try:
            async with WhatsAppPlaywright(headless=self.headless) as wa:
                success = await wa.send_message(contact_name, message)

                if success:
                    logger.info(f"✅ WhatsApp message sent to {contact_name}")
                    log_action(
                        "whatsapp_message_sent",
                        contact_name,
                        {
                            "message_length": len(message),
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        result="success"
                    )
                    return {
                        "success": True,
                        "contact": contact_name,
                        "message": message[:100] + "..." if len(message) > 100 else message
                    }
                else:
                    logger.error(f"❌ Failed to send message to {contact_name}")
                    log_action("whatsapp_send_failed", contact_name, result="error")
                    return {
                        "success": False,
                        "error": "Failed to send message"
                    }

        except Exception as e:
            logger.error(f"❌ WhatsApp error: {e}")
            log_action("whatsapp_error", str(e), result="error")
            return {"success": False, "error": str(e)}

    async def send_media(
        self,
        contact_name: str,
        media_path: str,
        caption: str = ""
    ) -> Dict:
        """
        Send image or video with optional caption

        Args:
            contact_name: Name of contact
            media_path: Path to image/video file
            caption: Optional caption text

        Returns:
            Dict with status
        """
        try:
            if not os.path.exists(media_path):
                return {
                    "success": False,
                    "error": f"Media file not found: {media_path}"
                }

            async with WhatsAppPlaywright(headless=self.headless) as wa:
                success = await wa.send_media(contact_name, media_path, caption)

                if success:
                    logger.info(f"✅ Media sent to {contact_name}")
                    log_action(
                        "whatsapp_media_sent",
                        contact_name,
                        {
                            "media_path": media_path,
                            "has_caption": bool(caption),
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        result="success"
                    )
                    return {
                        "success": True,
                        "contact": contact_name,
                        "media": os.path.basename(media_path),
                        "caption": caption[:50] + "..." if len(caption) > 50 else caption
                    }
                else:
                    logger.error(f"❌ Failed to send media to {contact_name}")
                    return {"success": False, "error": "Failed to send media"}

        except Exception as e:
            logger.error(f"❌ Send media error: {e}")
            return {"success": False, "error": str(e)}

    async def read_messages(
        self,
        contact_name: str,
        limit: int = 10
    ) -> Dict:
        """
        Read messages from a contact

        Args:
            contact_name: Name of contact
            limit: Number of messages to read

        Returns:
            Dict with messages list
        """
        try:
            async with WhatsAppPlaywright(headless=self.headless) as wa:
                messages = await wa.read_messages(contact_name, limit)

                if messages:
                    logger.info(f"✅ Read {len(messages)} messages from {contact_name}")
                    return {
                        "success": True,
                        "contact": contact_name,
                        "messages": messages,
                        "count": len(messages)
                    }
                else:
                    logger.info(f"ℹ️ No messages from {contact_name}")
                    return {
                        "success": True,
                        "contact": contact_name,
                        "messages": [],
                        "count": 0
                    }

        except Exception as e:
            logger.error(f"❌ Read messages error: {e}")
            return {"success": False, "error": str(e)}

    async def get_status(self, contact_name: str) -> Dict:
        """
        Get last seen/online status of a contact

        Args:
            contact_name: Name of contact

        Returns:
            Dict with status
        """
        try:
            async with WhatsAppPlaywright(headless=self.headless) as wa:
                status = await wa.get_status(contact_name)

                if status:
                    logger.info(f"ℹ️ {contact_name} status: {status}")
                    return {
                        "success": True,
                        "contact": contact_name,
                        "status": status
                    }
                else:
                    logger.info(f"ℹ️ Could not get status for {contact_name}")
                    return {
                        "success": True,
                        "contact": contact_name,
                        "status": "unknown"
                    }

        except Exception as e:
            logger.error(f"❌ Get status error: {e}")
            return {"success": False, "error": str(e)}

    async def react_to_message(self, emoji: str) -> Dict:
        """
        React to the last message with an emoji

        Args:
            emoji: Emoji to react with

        Returns:
            Dict with status
        """
        try:
            async with WhatsAppPlaywright(headless=self.headless) as wa:
                success = await wa.react_to_message(emoji)

                if success:
                    logger.info(f"✅ Reacted with {emoji}")
                    log_action("whatsapp_reaction_added", "whatsapp", {"emoji": emoji}, result="success")
                    return {
                        "success": True,
                        "emoji": emoji,
                        "message": "Reaction added successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to react"
                    }

        except Exception as e:
            logger.error(f"❌ React error: {e}")
            return {"success": False, "error": str(e)}

    def get_automation_status(self) -> Dict:
        """Get WhatsApp automation status"""
        return {
            "authenticated": True,  # Logged in via QR
            "type": "playwright_local",
            "headless": self.headless,
            "session_location": "~/.whatsapp_session/state.json"
        }


# Singleton instance
_whatsapp_server = None


def get_whatsapp_playwright_server() -> WhatsAppMCPPlaywright:
    """Get or create singleton WhatsApp Playwright server"""
    global _whatsapp_server
    if _whatsapp_server is None:
        _whatsapp_server = WhatsAppMCPPlaywright()
    return _whatsapp_server


def send_message(contact_name: str, message: str) -> Dict:
    """Convenience function to send WhatsApp message"""
    server = get_whatsapp_playwright_server()
    return safe_async_run(server.send_message(contact_name, message))


def send_media(contact_name: str, media_path: str, caption: str = "") -> Dict:
    """Convenience function to send WhatsApp media"""
    server = get_whatsapp_playwright_server()
    return safe_async_run(server.send_media(contact_name, media_path, caption))


def read_messages(contact_name: str, limit: int = 10) -> Dict:
    """Convenience function to read WhatsApp messages"""
    server = get_whatsapp_playwright_server()
    return safe_async_run(server.read_messages(contact_name, limit))
