"""
LinkedIn Automation Processor
Handles LinkedIn posting, messaging, and engagement tasks
Integrates with Playwright-based MCP server for local automation
"""

import asyncio
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict

from src.mcp_servers.linkedin_mcp_playwright import get_linkedin_playwright_server
from src.utils import setup_logger, log_action

logger = setup_logger("linkedin_processor")


class LinkedInAutomationProcessor:
    """Process LinkedIn automation tasks from vault files"""

    def __init__(self):
        """Initialize processor with LinkedIn MCP server"""
        self.mcp_server = get_linkedin_playwright_server()

    def process_post_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a LinkedIn post task

        Args:
            metadata: Task metadata (from frontmatter)
            content: Post content and instructions

        Returns:
            Result dict with success status
        """
        try:
            # Extract post content from task description
            post_text = self._extract_section(content, "Post Content")
            image_path = self._extract_field(content, "Image Path")

            if not post_text:
                return {
                    "success": False,
                    "error": "No post content found in task"
                }

            # Post to LinkedIn
            result = asyncio.run(self.mcp_server.post_to_feed(post_text, image_path))

            if result.get("success"):
                log_action(
                    "linkedin_post_processed",
                    "linkedin_processor",
                    {
                        "task_type": "post",
                        "content_length": len(post_text),
                        "has_image": bool(image_path),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    result="success"
                )
                return {
                    "success": True,
                    "action": "post_created",
                    "summary": f"Posted to LinkedIn: {post_text[:50]}...",
                    "content": post_text
                }
            else:
                logger.error(f"LinkedIn post failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Post failed")
                }

        except Exception as e:
            logger.exception(f"Error processing LinkedIn post task: {e}")
            return {"success": False, "error": str(e)}

    def process_message_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a LinkedIn direct message task

        Args:
            metadata: Task metadata
            content: Message content and recipient

        Returns:
            Result dict
        """
        try:
            recipient = self._extract_field(content, "Recipient")
            message = self._extract_section(content, "Message Content")

            if not recipient or not message:
                return {
                    "success": False,
                    "error": "Recipient and message required"
                }

            # Send message
            result = asyncio.run(self.mcp_server.send_message(recipient, message))

            if result.get("success"):
                log_action(
                    "linkedin_message_processed",
                    "linkedin_processor",
                    {
                        "task_type": "message",
                        "recipient": recipient,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    result="success"
                )
                return {
                    "success": True,
                    "action": "message_sent",
                    "summary": f"Message sent to {recipient}",
                    "recipient": recipient
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Failed to send message")
                }

        except Exception as e:
            logger.exception(f"Error processing LinkedIn message task: {e}")
            return {"success": False, "error": str(e)}

    def process_engagement_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process LinkedIn engagement task (like, comment, engage)

        Args:
            metadata: Task metadata
            content: Engagement instructions

        Returns:
            Result dict
        """
        try:
            action = self._extract_field(content, "Action")

            if action == "like":
                post_index = int(self._extract_field(content, "Post Index", "0"))
                result = asyncio.run(self.mcp_server.like_post(post_index))

                if result.get("success"):
                    return {
                        "success": True,
                        "action": "post_liked",
                        "summary": f"Liked post #{post_index}"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Failed to like")
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported engagement action: {action}"
                }

        except Exception as e:
            logger.exception(f"Error processing LinkedIn engagement task: {e}")
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


def process_linkedin_task(meta_path: Path) -> bool:
    """
    Main entry point for processing LinkedIn tasks from orchestrator

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
        processor = LinkedInAutomationProcessor()
        task_type = metadata.get("task_type", "post").lower()

        if task_type == "post":
            result = processor.process_post_task(metadata, task_content)
        elif task_type == "message":
            result = processor.process_message_task(metadata, task_content)
        elif task_type == "engagement":
            result = processor.process_engagement_task(metadata, task_content)
        else:
            result = {"success": False, "error": f"Unknown task type: {task_type}"}

        # Update metadata file with result
        if result.get("success"):
            _update_metadata(meta_path, {
                "status": "done",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "result": "success"
            })
            logger.info(f"✅ LinkedIn task processed: {result.get('summary')}")
            return True
        else:
            _update_metadata(meta_path, {
                "status": "failed",
                "error": result.get("error"),
                "failed_at": datetime.now(timezone.utc).isoformat()
            })
            logger.error(f"❌ LinkedIn task failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.exception(f"Error processing LinkedIn task: {e}")
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
