"""
Gmail Automation using App Password
Handles: Send, Read, Draft, Delete, Search, Label, Archive, Spam
"""

import os
import base64
import json
from typing import Optional, Dict, List
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from imapclient import IMAPClient
import logging

logger = logging.getLogger(__name__)

class GmailAppPassword:
    def __init__(self, email: str, app_password: str):
        """
        Initialize Gmail automation with App Password

        App Password Setup:
        1. Go to https://myaccount.google.com/
        2. Security → App passwords
        3. Select Mail and Windows Computer
        4. Copy the generated 16-character password
        """
        self.email = email
        self.app_password = app_password
        self.smtp_server = "smtp.gmail.com"
        self.imap_server = "imap.gmail.com"
        self.imap = None

    def connect_imap(self) -> bool:
        """Connect to Gmail IMAP"""
        try:
            self.imap = IMAPClient(self.imap_server, ssl=True)
            self.imap.login(self.email, self.app_password)
            logger.info("✅ Connected to Gmail IMAP")
            return True
        except Exception as e:
            logger.error(f"❌ IMAP connection failed: {e}")
            return False

    def send_email(self, to: str, subject: str, body: str,
                   attachments: List[str] = None, is_html: bool = False) -> bool:
        """Send an email"""
        try:
            # Create message
            msg = MIMEMultipart("alternative") if is_html else MIMEText(body)

            msg["Subject"] = subject
            msg["From"] = self.email
            msg["To"] = to

            # Add body
            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, "rb") as attachment:
                                part = MIMEBase("application", "octet-stream")
                                part.set_payload(attachment.read())
                                encoders.encode_base64(part)
                                part.add_header(
                                    "Content-Disposition",
                                    f"attachment; filename= {os.path.basename(file_path)}",
                                )
                                msg.attach(part)
                        except Exception as e:
                            logger.warning(f"Failed to attach {file_path}: {e}")

            # Send email
            with smtplib.SMTP_SSL(self.smtp_server, 465) as server:
                server.login(self.email, self.app_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def read_emails(self, folder: str = "INBOX", limit: int = 10,
                    unread_only: bool = False) -> List[Dict]:
        """Read emails from Gmail"""
        try:
            if not self.imap:
                if not self.connect_imap():
                    return []

            # Select folder
            self.imap.select_folder(folder)

            # Search criteria
            search_criteria = ["UNSEEN"] if unread_only else ["ALL"]
            message_ids = self.imap.search(search_criteria)

            # Get latest emails
            message_ids = sorted(message_ids)[-limit:]
            emails = []

            for msg_id in message_ids:
                try:
                    raw_message = self.imap.fetch(msg_id, ["RFC822"])
                    email_data = raw_message[msg_id][b"RFC822"]

                    # Parse email
                    from email import message_from_bytes
                    email_message = message_from_bytes(email_data)

                    email_dict = {
                        "id": msg_id,
                        "from": email_message.get("From", "Unknown"),
                        "subject": email_message.get("Subject", "(No Subject)"),
                        "date": email_message.get("Date", ""),
                        "body": self._get_email_body(email_message),
                        "timestamp": datetime.now().isoformat()
                    }
                    emails.append(email_dict)
                except Exception as e:
                    logger.warning(f"Failed to parse email {msg_id}: {e}")

            logger.info(f"✅ Read {len(emails)} emails from {folder}")
            return emails
        except Exception as e:
            logger.error(f"❌ Failed to read emails: {e}")
            return []

    def search_emails(self, query: str, folder: str = "INBOX", limit: int = 20) -> List[Dict]:
        """Search emails by query (e.g., 'from:someone@example.com', 'subject:meeting')"""
        try:
            if not self.imap:
                if not self.connect_imap():
                    return []

            self.imap.select_folder(folder)

            # Convert Gmail search syntax to IMAP
            if "from:" in query:
                imap_query = query.replace("from:", "FROM")
            elif "subject:" in query:
                imap_query = query.replace("subject:", "SUBJECT")
            else:
                imap_query = f"TEXT {query}"

            message_ids = self.imap.search([imap_query])
            message_ids = sorted(message_ids)[-limit:]

            emails = []
            for msg_id in message_ids:
                try:
                    raw_message = self.imap.fetch(msg_id, ["RFC822"])
                    email_data = raw_message[msg_id][b"RFC822"]

                    from email import message_from_bytes
                    email_message = message_from_bytes(email_data)

                    email_dict = {
                        "id": msg_id,
                        "from": email_message.get("From"),
                        "subject": email_message.get("Subject"),
                        "date": email_message.get("Date"),
                        "preview": self._get_email_body(email_message)[:100]
                    }
                    emails.append(email_dict)
                except Exception as e:
                    logger.warning(f"Failed to parse search result {msg_id}: {e}")

            logger.info(f"✅ Found {len(emails)} emails matching '{query}'")
            return emails
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []

    def create_draft(self, to: str, subject: str, body: str) -> bool:
        """Create a draft email (saved locally)"""
        try:
            draft = {
                "to": to,
                "subject": subject,
                "body": body,
                "created_at": datetime.now().isoformat()
            }

            draft_file = f"/tmp/gmail_draft_{int(datetime.now().timestamp())}.json"
            with open(draft_file, 'w') as f:
                json.dump(draft, f)

            logger.info(f"✅ Draft created: {draft_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create draft: {e}")
            return False

    def mark_as_read(self, message_ids: List[int]) -> bool:
        """Mark emails as read"""
        try:
            if not self.imap:
                if not self.connect_imap():
                    return False

            self.imap.set_flags(message_ids, [b"\\Seen"])
            logger.info(f"✅ Marked {len(message_ids)} emails as read")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark as read: {e}")
            return False

    def delete_email(self, message_ids: List[int]) -> bool:
        """Delete emails"""
        try:
            if not self.imap:
                if not self.connect_imap():
                    return False

            self.imap.set_flags(message_ids, [b"\\Deleted"])
            self.imap.expunge()
            logger.info(f"✅ Deleted {len(message_ids)} emails")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete emails: {e}")
            return False

    def add_label(self, message_ids: List[int], label: str) -> bool:
        """Add a label/folder to emails"""
        try:
            if not self.imap:
                if not self.connect_imap():
                    return False

            # Gmail labels are case-sensitive
            label_name = f"[Gmail]/{label}".encode() if label in ["Important", "Starred"] else label.encode()
            self.imap.copy(message_ids, label_name)
            logger.info(f"✅ Added label '{label}' to {len(message_ids)} emails")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to add label: {e}")
            return False

    def archive_email(self, message_ids: List[int]) -> bool:
        """Archive emails (move from Inbox)"""
        try:
            if not self.imap:
                if not self.connect_imap():
                    return False

            self.imap.select_folder("INBOX")
            self.imap.move(message_ids, "[Gmail]/All Mail")
            logger.info(f"✅ Archived {len(message_ids)} emails")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to archive: {e}")
            return False

    def move_to_spam(self, message_ids: List[int]) -> bool:
        """Move emails to spam"""
        try:
            if not self.imap:
                if not self.connect_imap():
                    return False

            self.imap.move(message_ids, "[Gmail]/Spam")
            logger.info(f"✅ Moved {len(message_ids)} emails to spam")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to move to spam: {e}")
            return False

    def _get_email_body(self, email_message) -> str:
        """Extract email body text"""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        return part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            pass
        return ""

    def close(self):
        """Close IMAP connection"""
        if self.imap:
            self.imap.logout()
            logger.info("Gmail IMAP connection closed")


def main():
    """Test Gmail automation"""
    email = os.getenv("GMAIL_EMAIL")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not email or not app_password:
        logger.error("❌ Set GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables")
        return

    gmail = GmailAppPassword(email, app_password)

    try:
        # Send email
        gmail.send_email(
            to="test@example.com",
            subject="Test Email from Automation",
            body="This is a test email sent using Gmail App Password automation.",
        )

        # Read emails
        emails = gmail.read_emails("INBOX", limit=5, unread_only=False)
        for email_msg in emails:
            print(f"📧 {email_msg['from']}: {email_msg['subject']}")

        # Search emails
        search_results = gmail.search_emails("from:boss@company.com", limit=5)
        print(f"\n🔍 Found {len(search_results)} emails from boss")

        # Create draft
        gmail.create_draft(
            to="recipient@example.com",
            subject="Draft Email",
            body="This is a draft that will be saved."
        )

    finally:
        gmail.close()


if __name__ == "__main__":
    main()
