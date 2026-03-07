"""
Gmail Automation Processor
Handles Gmail sending, reading, searching, and organizing tasks
Integrates with App Password-based MCP server for IMAP/SMTP automation
"""

import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List

from src.mcp_servers.gmail_mcp_apppassword import get_gmail_apppassword_server
from src.utils import setup_logger, log_action

logger = setup_logger("gmail_processor")


class GmailAutomationProcessor:
    """Process Gmail automation tasks from vault files"""

    def __init__(self):
        """Initialize processor with Gmail MCP server"""
        self.mcp_server = get_gmail_apppassword_server()

    def process_send_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a Gmail send email task

        Args:
            metadata: Task metadata (from frontmatter)
            content: Email details and body

        Returns:
            Result dict with success status
        """
        try:
            recipient = self._extract_field(content, "To")
            subject = self._extract_field(content, "Subject")
            body = self._extract_section(content, "Email Body")
            cc = self._extract_field(content, "CC", "")
            bcc = self._extract_field(content, "BCC", "")

            if not recipient or not subject or not body:
                return {
                    "success": False,
                    "error": "Recipient, subject, and body required"
                }

            # Parse attachments if any
            attachments_str = self._extract_field(content, "Attachments", "")
            attachments = [a.strip() for a in attachments_str.split(",") if a.strip()]

            # Send email
            result = self.mcp_server.send_email(
                to=recipient,
                subject=subject,
                body=body,
                attachments=attachments if attachments else None,
                is_html=self._is_html(content)
            )

            if result.get("success"):
                log_action(
                    "gmail_send_processed",
                    "gmail_processor",
                    {
                        "task_type": "send",
                        "to": recipient,
                        "subject": subject,
                        "has_attachments": len(attachments) > 0,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    result="success"
                )
                return {
                    "success": True,
                    "action": "email_sent",
                    "summary": f"Email sent to {recipient}: {subject}",
                    "to": recipient,
                    "subject": subject
                }
            else:
                logger.error(f"Gmail send failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Send failed")
                }

        except Exception as e:
            logger.exception(f"Error processing Gmail send task: {e}")
            return {"success": False, "error": str(e)}

    def process_draft_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a Gmail draft creation task

        Args:
            metadata: Task metadata
            content: Draft details

        Returns:
            Result dict
        """
        try:
            recipient = self._extract_field(content, "To")
            subject = self._extract_field(content, "Subject")
            body = self._extract_section(content, "Email Body")

            if not recipient or not subject or not body:
                return {
                    "success": False,
                    "error": "Recipient, subject, and body required"
                }

            # Create draft
            result = self.mcp_server.create_draft(recipient, subject, body)

            if result.get("success"):
                log_action(
                    "gmail_draft_processed",
                    "gmail_processor",
                    {
                        "task_type": "draft",
                        "to": recipient,
                        "subject": subject,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    result="success"
                )
                return {
                    "success": True,
                    "action": "draft_created",
                    "summary": f"Draft created for {recipient}: {subject}",
                    "to": recipient,
                    "subject": subject
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Draft creation failed")
                }

        except Exception as e:
            logger.exception(f"Error processing Gmail draft task: {e}")
            return {"success": False, "error": str(e)}

    def process_read_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a Gmail read/search task

        Args:
            metadata: Task metadata
            content: Search/read instructions

        Returns:
            Result dict with emails
        """
        try:
            action = self._extract_field(content, "Action", "read").lower()
            folder = self._extract_field(content, "Folder", "INBOX")
            limit = int(self._extract_field(content, "Limit", "10"))

            if action == "search":
                query = self._extract_field(content, "Query")
                if not query:
                    return {"success": False, "error": "Query required for search"}

                result = self.mcp_server.search_emails(query, folder, limit)
            else:  # read
                unread_only = self._extract_field(content, "Unread Only", "false").lower() == "true"
                result = self.mcp_server.read_emails(folder, limit, unread_only)

            if result.get("success"):
                emails = result.get("emails", [])
                log_action(
                    "gmail_read_processed",
                    "gmail_processor",
                    {
                        "task_type": "read",
                        "action": action,
                        "folder": folder,
                        "count": len(emails),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    result="success"
                )
                return {
                    "success": True,
                    "action": f"emails_{action}",
                    "summary": f"Found {len(emails)} emails",
                    "emails": emails,
                    "count": len(emails)
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Read/search failed")
                }

        except Exception as e:
            logger.exception(f"Error processing Gmail read task: {e}")
            return {"success": False, "error": str(e)}

    def process_organize_task(self, metadata: Dict, content: str) -> Dict:
        """
        Process a Gmail organize task (archive, label, delete, etc)

        Args:
            metadata: Task metadata
            content: Organization instructions

        Returns:
            Result dict
        """
        try:
            action = self._extract_field(content, "Action", "archive").lower()
            query = self._extract_field(content, "Query")
            label = self._extract_field(content, "Label", "")

            if not query:
                return {"success": False, "error": "Query required"}

            # First, search for matching emails
            search_result = self.mcp_server.search_emails(query, limit=100)
            if not search_result.get("success"):
                return {"success": False, "error": "Could not find emails to organize"}

            emails = search_result.get("emails", [])
            if not emails:
                return {
                    "success": True,
                    "action": "no_emails",
                    "summary": "No emails matched the query"
                }

            # Extract message IDs
            message_ids = [e.get("id") for e in emails if e.get("id")]

            # Apply action
            if action == "archive":
                result = self.mcp_server.archive_email(message_ids)
                action_name = "archived"
            elif action == "delete":
                result = self.mcp_server.delete_email(message_ids)
                action_name = "deleted"
            elif action == "label":
                if not label:
                    return {"success": False, "error": "Label required for label action"}
                result = self.mcp_server.add_label(message_ids, label)
                action_name = f"labeled '{label}'"
            elif action == "read":
                result = self.mcp_server.mark_as_read(message_ids)
                action_name = "marked as read"
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

            if result.get("success"):
                log_action(
                    "gmail_organize_processed",
                    "gmail_processor",
                    {
                        "task_type": "organize",
                        "action": action,
                        "query": query,
                        "count": len(message_ids),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    },
                    result="success"
                )
                return {
                    "success": True,
                    "action": action,
                    "summary": f"{len(message_ids)} emails {action_name}",
                    "count": len(message_ids)
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", f"Failed to {action}")
                }

        except Exception as e:
            logger.exception(f"Error processing Gmail organize task: {e}")
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
        pattern = rf"**{field_name}:**\s*(.+?)(?:\n|$)"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return default

    def _is_html(self, content: str) -> bool:
        """Check if email body should be HTML"""
        return "html" in self._extract_field(content, "Format", "").lower()


def process_gmail_task(meta_path: Path) -> bool:
    """
    Main entry point for processing Gmail tasks from orchestrator

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
        processor = GmailAutomationProcessor()
        task_type = metadata.get("task_type", "send").lower()

        if task_type == "send":
            result = processor.process_send_task(metadata, task_content)
        elif task_type == "draft":
            result = processor.process_draft_task(metadata, task_content)
        elif task_type == "read":
            result = processor.process_read_task(metadata, task_content)
        elif task_type == "organize":
            result = processor.process_organize_task(metadata, task_content)
        else:
            result = {"success": False, "error": f"Unknown task type: {task_type}"}

        # Update metadata file with result
        if result.get("success"):
            _update_metadata(meta_path, {
                "status": "done",
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "result": "success"
            })
            logger.info(f"✅ Gmail task processed: {result.get('summary')}")
            return True
        else:
            _update_metadata(meta_path, {
                "status": "failed",
                "error": result.get("error"),
                "failed_at": datetime.now(timezone.utc).isoformat()
            })
            logger.error(f"❌ Gmail task failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.exception(f"Error processing Gmail task: {e}")
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
