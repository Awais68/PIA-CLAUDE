"""
Gmail MCP Server - Real Email Sending Implementation
Uses Google Gmail API v1 to send actual emails
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_core.exceptions import GoogleAPIError
from googleapiclient.discovery import build

from src.config import PROJECT_ROOT
from src.utils.logging_utils import setup_logging, log_action, log_error

logger = setup_logging()

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailMCPServer:
    """Gmail MCP Server - Handles real email sending"""

    def __init__(self):
        """Initialize Gmail API client"""
        self.service = None
        self.credentials = None
        self._authenticate()

    def _authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0

        Returns:
            True if authenticated successfully
        """
        try:
            credentials_file = PROJECT_ROOT / "credentials.json"
            token_file = PROJECT_ROOT / "token.json"

            # Load existing token if available
            if token_file.exists():
                with open(token_file, 'rb') as token:
                    self.credentials = pickle.load(token)

            # Refresh or obtain new credentials
            if self.credentials and self.credentials.expired:
                self.credentials.refresh(Request())
            elif not self.credentials:
                if not credentials_file.exists():
                    logger.error("❌ credentials.json not found. Run OAuth setup first.")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_file), SCOPES)
                self.credentials = flow.run_local_server(port=0)

                # Save credentials for next time
                with open(token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("✅ Gmail authenticated successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Gmail authentication failed: {e}")
            log_error("gmail_auth_failed", str(e))
            return False

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
        html: bool = False
    ) -> bool:
        """
        Send email via Gmail API

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: True if body is HTML

        Returns:
            True if email sent successfully
        """
        try:
            if not self.service:
                if not self._authenticate():
                    return False

            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject

            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc

            # Add body
            mime_type = 'html' if html else 'plain'
            part = MIMEText(body, mime_type)
            message.attach(part)

            # Send
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            send_message = {'raw': raw}

            result = self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()

            logger.info(f"✅ Email sent to {to}: {subject}")
            log_action(
                "email_sent",
                to,
                "success",
                {
                    "subject": subject,
                    "message_id": result.get('id'),
                    "gmail": True
                }
            )
            return True

        except GoogleAPIError as e:
            logger.error(f"❌ Gmail API error: {e}")
            log_error("gmail_send_failed", str(e), {"to": to, "subject": subject})
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            log_error("email_send_failed", str(e), {"to": to})
            return False

    def get_quota(self) -> dict:
        """Get Gmail API quota info"""
        try:
            if not self.service:
                return {"status": "not_authenticated"}

            settings = self.service.users().settings().get(userId='me').execute()
            return {
                "status": "ok",
                "forwarding_address": settings.get('forwardingAddress')
            }
        except Exception as e:
            logger.error(f"Failed to get quota: {e}")
            return {"status": "error", "error": str(e)}


# Singleton instance
_gmail_server = None


def get_gmail_server() -> GmailMCPServer:
    """Get or create singleton Gmail server"""
    global _gmail_server
    if _gmail_server is None:
        _gmail_server = GmailMCPServer()
    return _gmail_server


def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    html: bool = False
) -> bool:
    """Convenience function to send email"""
    server = get_gmail_server()
    return server.send_email(to, subject, body, cc, bcc, html)
