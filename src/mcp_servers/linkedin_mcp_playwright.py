"""
LinkedIn MCP Server - Playwright-based Implementation
Uses local browser automation instead of LinkedIn API
Ideal for personal automation and bypassing API rate limits
"""

import asyncio
import os
from datetime import datetime
from typing import Optional, Dict, List

from src.automations.linkedin_playwright import LinkedInPlaywright
from src.playwright_utils import safe_async_run
from src.utils import setup_logger, log_action

logger = setup_logger("linkedin_playwright")


class LinkedInMCPPlaywright:
    """LinkedIn MCP Server - Handles browser-based LinkedIn automation"""

    def __init__(self):
        """Initialize LinkedIn Playwright client"""
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.authenticated = bool(self.email and self.password)

    async def post_to_feed(
        self,
        content: str,
        image_path: Optional[str] = None
    ) -> Dict:
        """
        Post content to LinkedIn feed

        Args:
            content: Post text content
            image_path: Optional path to image to attach

        Returns:
            Dict with status and result
        """
        try:
            if not self.authenticated:
                return {
                    "success": False,
                    "error": "LinkedIn not authenticated. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD."
                }

            async with LinkedInPlaywright(
                email=self.email,
                password=self.password,
                headless=True
            ) as li:
                success = await li.post_update(content, image_path)

                if success:
                    logger.info(f"✅ Posted to LinkedIn feed: {content[:50]}...")
                    log_action(
                        "linkedin_post_created",
                        "linkedin_playwright",
                        {
                            "content_length": len(content),
                            "has_image": image_path is not None,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        result="success"
                    )
                    return {
                        "success": True,
                        "content": content[:100] + "..." if len(content) > 100 else content
                    }
                else:
                    logger.error("❌ Failed to post to LinkedIn")
                    log_action("linkedin_post_failed", "linkedin_playwright", result="error")
                    return {
                        "success": False,
                        "error": "Failed to post content"
                    }

        except Exception as e:
            logger.error(f"❌ LinkedIn Playwright error: {e}")
            log_action("linkedin_error", str(e), result="error")
            return {"success": False, "error": str(e)}

    async def read_feed(self, limit: int = 10) -> Dict:
        """
        Read posts from LinkedIn feed

        Args:
            limit: Number of posts to read (default 10)

        Returns:
            Dict with posts list
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            async with LinkedInPlaywright(
                email=self.email,
                password=self.password,
                headless=True
            ) as li:
                posts = await li.read_feed(limit)
                logger.info(f"✅ Read {len(posts)} posts from LinkedIn feed")
                return {
                    "success": True,
                    "posts": posts,
                    "count": len(posts)
                }

        except Exception as e:
            logger.error(f"❌ Failed to read feed: {e}")
            return {"success": False, "error": str(e)}

    async def like_post(self, post_index: int = 0) -> Dict:
        """
        Like a post from the feed

        Args:
            post_index: Index of post to like (default 0)

        Returns:
            Dict with status
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            async with LinkedInPlaywright(
                email=self.email,
                password=self.password,
                headless=True
            ) as li:
                success = await li.like_post(post_index)
                if success:
                    logger.info(f"✅ Liked post #{post_index}")
                    log_action("linkedin_post_liked", "linkedin_playwright", result="success")
                    return {"success": True, "post_index": post_index}
                else:
                    logger.error(f"❌ Failed to like post #{post_index}")
                    return {"success": False, "error": "Could not like post"}

        except Exception as e:
            logger.error(f"❌ Like post error: {e}")
            return {"success": False, "error": str(e)}

    async def send_message(
        self,
        recipient_name: str,
        message: str
    ) -> Dict:
        """
        Send direct message to a LinkedIn contact

        Args:
            recipient_name: Name of recipient
            message: Message text

        Returns:
            Dict with status
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            async with LinkedInPlaywright(
                email=self.email,
                password=self.password,
                headless=True
            ) as li:
                success = await li.send_message(recipient_name, message)

                if success:
                    logger.info(f"✅ Message sent to {recipient_name}")
                    log_action(
                        "linkedin_message_sent",
                        recipient_name,
                        {"message_length": len(message)},
                        result="success"
                    )
                    return {
                        "success": True,
                        "recipient": recipient_name,
                        "message": message[:100] + "..." if len(message) > 100 else message
                    }
                else:
                    logger.error(f"❌ Failed to send message to {recipient_name}")
                    return {"success": False, "error": "Failed to send message"}

        except Exception as e:
            logger.error(f"❌ Send message error: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict:
        """Get LinkedIn automation status"""
        return {
            "authenticated": self.authenticated,
            "email": self.email if self.authenticated else "not_set",
            "type": "playwright_local"
        }


# Singleton instance
_linkedin_server = None


def get_linkedin_playwright_server() -> LinkedInMCPPlaywright:
    """Get or create singleton LinkedIn Playwright server"""
    global _linkedin_server
    if _linkedin_server is None:
        _linkedin_server = LinkedInMCPPlaywright()
    return _linkedin_server


def post_to_feed(content: str, image_path: Optional[str] = None) -> Dict:
    """Convenience function to post to LinkedIn feed"""
    server = get_linkedin_playwright_server()
    return safe_async_run(server.post_to_feed(content, image_path))


def read_feed(limit: int = 10) -> Dict:
    """Convenience function to read LinkedIn feed"""
    server = get_linkedin_playwright_server()
    return safe_async_run(server.read_feed(limit))


def send_message(recipient_name: str, message: str) -> Dict:
    """Convenience function to send LinkedIn message"""
    server = get_linkedin_playwright_server()
    return safe_async_run(server.send_message(recipient_name, message))
