"""
MCP Client Stubs - Local Agent
Interfaces to external services (email, social, WhatsApp, browser)
"""

from .email_client import (
    EmailMCPClient,
    get_email_client,
    send_email
)

from .social_client import (
    SocialMediaMCPClient,
    get_social_client,
    post_to_platform
)

from .whatsapp_client import (
    WhatsAppMCPClient,
    get_whatsapp_client,
    send_message,
    send_alert
)

from .browser_client import (
    BrowserMCPClient,
    get_browser_client,
    execute_payment
)

__all__ = [
    "EmailMCPClient",
    "get_email_client",
    "send_email",
    "SocialMediaMCPClient",
    "get_social_client",
    "post_to_platform",
    "WhatsAppMCPClient",
    "get_whatsapp_client",
    "send_message",
    "send_alert",
    "BrowserMCPClient",
    "get_browser_client",
    "execute_payment",
]
