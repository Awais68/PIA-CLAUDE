"""
WhatsApp MCP Server - Real Message Sending Implementation
Uses Meta WhatsApp Business Cloud API to send actual messages
"""

import requests
from datetime import datetime

from src.config import PROJECT_ROOT
from src.utils.logging_utils import setup_logging, log_action, log_error

logger = setup_logging()


class WhatsAppMCPServer:
    """WhatsApp MCP Server - Handles real WhatsApp messaging"""

    def __init__(self):
        """Initialize WhatsApp API client"""
        self.base_url = "https://graph.instagram.com/v18.0"
        self.whatsapp_token = None
        self.phone_number_id = None
        self.business_account_id = None

        self._load_credentials()
        self.authenticated = bool(self.whatsapp_token and self.phone_number_id)

    def _load_credentials(self):
        """Load WhatsApp credentials from environment"""
        import os
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")

        self.whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")

    def send_message(
        self,
        recipient_phone: str,
        message_text: str
    ) -> dict:
        """
        Send WhatsApp message to recipient

        Args:
            recipient_phone: Recipient phone number (with country code, e.g., +1234567890)
            message_text: Message text to send

        Returns:
            Dict with status and message ID
        """
        try:
            if not self.authenticated:
                return {
                    "success": False,
                    "error": "WhatsApp not authenticated"
                }

            # Prepare message payload
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_phone,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_text
                }
            }

            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}",
                "Content-Type": "application/json"
            }

            url = f"{self.base_url}/{self.phone_number_id}/messages"

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                result = response.json()
                message_id = result.get('messages', [{}])[0].get('id', 'unknown')
                logger.info(f"✅ WhatsApp message sent to {recipient_phone}: {message_id}")
                log_action(
                    "whatsapp_message_sent",
                    recipient_phone,
                    "success",
                    {
                        "message_id": message_id,
                        "message_length": len(message_text),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return {
                    "success": True,
                    "message_id": message_id,
                    "recipient": recipient_phone,
                    "text": message_text[:50] + "..." if len(message_text) > 50 else message_text
                }
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                logger.error(f"❌ WhatsApp API error: {error_msg}")
                log_error("whatsapp_send_failed", error_msg, {"to": recipient_phone})
                return {
                    "success": False,
                    "error": error_msg
                }

        except requests.RequestException as e:
            logger.error(f"❌ WhatsApp request failed: {e}")
            log_error("whatsapp_request_failed", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {e}")
            log_error("whatsapp_failed", str(e))
            return {"success": False, "error": str(e)}

    def send_alert(
        self,
        recipient_phone: str,
        alert_type: str,
        alert_message: str
    ) -> dict:
        """
        Send WhatsApp alert to recipient

        Args:
            recipient_phone: Recipient phone number
            alert_type: Alert severity (WARNING, CRITICAL, EMERGENCY)
            alert_message: Alert message

        Returns:
            Dict with status and message ID
        """
        formatted_message = f"🚨 [{alert_type}]\n{alert_message}"
        return self.send_message(recipient_phone, formatted_message)

    def get_account_info(self) -> dict:
        """Get WhatsApp business account info"""
        try:
            if not self.authenticated:
                return {"authenticated": False}

            return {
                "authenticated": True,
                "phone_number_id": self.phone_number_id,
                "business_account_id": self.business_account_id,
                "status": "connected"
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {"authenticated": False, "error": str(e)}


# Singleton instance
_whatsapp_server = None


def get_whatsapp_server() -> WhatsAppMCPServer:
    """Get or create singleton WhatsApp server"""
    global _whatsapp_server
    if _whatsapp_server is None:
        _whatsapp_server = WhatsAppMCPServer()
    return _whatsapp_server


def send_message(recipient_phone: str, message_text: str) -> dict:
    """Convenience function to send WhatsApp message"""
    server = get_whatsapp_server()
    return server.send_message(recipient_phone, message_text)


def send_alert(recipient_phone: str, alert_type: str, alert_message: str) -> dict:
    """Convenience function to send WhatsApp alert"""
    server = get_whatsapp_server()
    return server.send_alert(recipient_phone, alert_type, alert_message)
