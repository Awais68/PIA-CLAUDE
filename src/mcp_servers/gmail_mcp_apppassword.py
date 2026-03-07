"""
Gmail MCP Server - App Password Implementation
Uses IMAP/SMTP with Gmail App Password for local email automation
Ideal for simple email operations without OAuth complexity
"""

import os
from datetime import datetime
from typing import Optional, Dict, List

from src.automations.gmail_app_password import GmailAppPassword
from src.utils import setup_logger, log_action

logger = setup_logger("gmail_apppassword")


class GmailMCPAppPassword:
    """Gmail MCP Server - Handles email via IMAP/SMTP with App Password"""

    def __init__(self):
        """Initialize Gmail App Password client"""
        self.email = os.getenv("GMAIL_EMAIL")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")
        self.authenticated = bool(self.email and self.app_password)

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        is_html: bool = False
    ) -> Dict:
        """
        Send email via Gmail

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            attachments: Optional list of file paths to attach
            is_html: Whether body is HTML (default: plain text)

        Returns:
            Dict with status
        """
        try:
            if not self.authenticated:
                return {
                    "success": False,
                    "error": "Gmail not authenticated. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD."
                }

            gmail = GmailAppPassword(self.email, self.app_password)

            try:
                success = gmail.send_email(
                    to=to,
                    subject=subject,
                    body=body,
                    attachments=attachments,
                    is_html=is_html
                )

                if success:
                    logger.info(f"✅ Email sent to {to}: {subject}")
                    log_action(
                        "email_sent",
                        to,
                        {
                            "subject": subject,
                            "has_attachments": bool(attachments),
                            "is_html": is_html,
                            "timestamp": datetime.utcnow().isoformat()
                        },
                        result="success"
                    )
                    return {
                        "success": True,
                        "to": to,
                        "subject": subject,
                        "message": "Email sent successfully"
                    }
                else:
                    logger.error(f"❌ Failed to send email to {to}")
                    log_action("email_send_failed", to, {"subject": subject}, result="error")
                    return {
                        "success": False,
                        "error": "Failed to send email"
                    }

            finally:
                gmail.close()

        except Exception as e:
            logger.error(f"❌ Gmail error: {e}")
            log_action("gmail_error", str(e), result="error")
            return {"success": False, "error": str(e)}

    def read_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False
    ) -> Dict:
        """
        Read emails from Gmail

        Args:
            folder: Folder name (default: INBOX)
            limit: Number of emails to read
            unread_only: Only read unread emails

        Returns:
            Dict with emails list
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            gmail = GmailAppPassword(self.email, self.app_password)

            try:
                emails = gmail.read_emails(folder, limit, unread_only)

                if emails:
                    logger.info(f"✅ Read {len(emails)} emails from {folder}")
                    return {
                        "success": True,
                        "folder": folder,
                        "emails": emails,
                        "count": len(emails)
                    }
                else:
                    logger.info(f"ℹ️ No emails found in {folder}")
                    return {
                        "success": True,
                        "folder": folder,
                        "emails": [],
                        "count": 0
                    }

            finally:
                gmail.close()

        except Exception as e:
            logger.error(f"❌ Read emails error: {e}")
            return {"success": False, "error": str(e)}

    def search_emails(
        self,
        query: str,
        folder: str = "INBOX",
        limit: int = 20
    ) -> Dict:
        """
        Search emails in Gmail

        Args:
            query: Search query (e.g., "from:user@example.com", "subject:meeting")
            folder: Folder to search in (default: INBOX)
            limit: Maximum results

        Returns:
            Dict with search results
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            gmail = GmailAppPassword(self.email, self.app_password)

            try:
                results = gmail.search_emails(query, folder, limit)

                if results:
                    logger.info(f"✅ Found {len(results)} emails matching '{query}'")
                    return {
                        "success": True,
                        "query": query,
                        "results": results,
                        "count": len(results)
                    }
                else:
                    logger.info(f"ℹ️ No emails match '{query}'")
                    return {
                        "success": True,
                        "query": query,
                        "results": [],
                        "count": 0
                    }

            finally:
                gmail.close()

        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return {"success": False, "error": str(e)}

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str
    ) -> Dict:
        """
        Create a draft email

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body

        Returns:
            Dict with status
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            gmail = GmailAppPassword(self.email, self.app_password)

            try:
                success = gmail.create_draft(to, subject, body)

                if success:
                    logger.info(f"✅ Draft created for {to}: {subject}")
                    log_action(
                        "draft_created",
                        to,
                        {"subject": subject},
                        result="success"
                    )
                    return {
                        "success": True,
                        "to": to,
                        "subject": subject,
                        "message": "Draft created successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to create draft"
                    }

            finally:
                gmail.close()

        except Exception as e:
            logger.error(f"❌ Draft creation error: {e}")
            return {"success": False, "error": str(e)}

    def archive_email(self, message_ids: List[int]) -> Dict:
        """
        Archive emails

        Args:
            message_ids: List of message IDs to archive

        Returns:
            Dict with status
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            gmail = GmailAppPassword(self.email, self.app_password)

            try:
                success = gmail.archive_email(message_ids)

                if success:
                    logger.info(f"✅ Archived {len(message_ids)} emails")
                    log_action("emails_archived", "gmail", {"count": len(message_ids)}, result="success")
                    return {
                        "success": True,
                        "count": len(message_ids),
                        "message": "Emails archived successfully"
                    }
                else:
                    return {"success": False, "error": "Failed to archive"}

            finally:
                gmail.close()

        except Exception as e:
            logger.error(f"❌ Archive error: {e}")
            return {"success": False, "error": str(e)}

    def mark_as_read(self, message_ids: List[int]) -> Dict:
        """
        Mark emails as read

        Args:
            message_ids: List of message IDs

        Returns:
            Dict with status
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            gmail = GmailAppPassword(self.email, self.app_password)

            try:
                success = gmail.mark_as_read(message_ids)

                if success:
                    logger.info(f"✅ Marked {len(message_ids)} emails as read")
                    log_action("emails_marked_read", "gmail", {"count": len(message_ids)}, result="success")
                    return {
                        "success": True,
                        "count": len(message_ids),
                        "message": "Marked as read successfully"
                    }
                else:
                    return {"success": False, "error": "Failed to mark as read"}

            finally:
                gmail.close()

        except Exception as e:
            logger.error(f"❌ Mark as read error: {e}")
            return {"success": False, "error": str(e)}

    def delete_email(self, message_ids: List[int]) -> Dict:
        """
        Delete emails

        Args:
            message_ids: List of message IDs to delete

        Returns:
            Dict with status
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            gmail = GmailAppPassword(self.email, self.app_password)

            try:
                success = gmail.delete_email(message_ids)

                if success:
                    logger.info(f"✅ Deleted {len(message_ids)} emails")
                    log_action("emails_deleted", "gmail", {"count": len(message_ids)}, result="success")
                    return {
                        "success": True,
                        "count": len(message_ids),
                        "message": "Emails deleted successfully"
                    }
                else:
                    return {"success": False, "error": "Failed to delete"}

            finally:
                gmail.close()

        except Exception as e:
            logger.error(f"❌ Delete error: {e}")
            return {"success": False, "error": str(e)}

    def add_label(self, message_ids: List[int], label: str) -> Dict:
        """
        Add label to emails

        Args:
            message_ids: List of message IDs
            label: Label name

        Returns:
            Dict with status
        """
        try:
            if not self.authenticated:
                return {"success": False, "error": "Not authenticated"}

            gmail = GmailAppPassword(self.email, self.app_password)

            try:
                success = gmail.add_label(message_ids, label)

                if success:
                    logger.info(f"✅ Added label '{label}' to {len(message_ids)} emails")
                    log_action(
                        "label_added",
                        "gmail",
                        {"label": label, "count": len(message_ids)},
                        result="success"
                    )
                    return {
                        "success": True,
                        "label": label,
                        "count": len(message_ids),
                        "message": "Label added successfully"
                    }
                else:
                    return {"success": False, "error": "Failed to add label"}

            finally:
                gmail.close()

        except Exception as e:
            logger.error(f"❌ Add label error: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict:
        """Get Gmail automation status"""
        return {
            "authenticated": self.authenticated,
            "email": self.email if self.authenticated else "not_set",
            "type": "app_password_imap",
            "requires_2fa": "Yes (for App Password generation)"
        }


# Singleton instance
_gmail_server = None


def get_gmail_apppassword_server() -> GmailMCPAppPassword:
    """Get or create singleton Gmail App Password server"""
    global _gmail_server
    if _gmail_server is None:
        _gmail_server = GmailMCPAppPassword()
    return _gmail_server


def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None,
    is_html: bool = False
) -> Dict:
    """Convenience function to send email"""
    server = get_gmail_apppassword_server()
    return server.send_email(to, subject, body, attachments, is_html)


def read_emails(folder: str = "INBOX", limit: int = 10, unread_only: bool = False) -> Dict:
    """Convenience function to read emails"""
    server = get_gmail_apppassword_server()
    return server.read_emails(folder, limit, unread_only)


def search_emails(query: str, folder: str = "INBOX", limit: int = 20) -> Dict:
    """Convenience function to search emails"""
    server = get_gmail_apppassword_server()
    return server.search_emails(query, folder, limit)
