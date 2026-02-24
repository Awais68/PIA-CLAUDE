"""
LinkedIn MCP Server - Real Post Implementation
Uses LinkedIn API v2 to post to company page
"""

import requests
from datetime import datetime

from src.config import (
    LINKEDIN_ACCESS_TOKEN,
    LINKEDIN_PAGE_ID
)
from src.utils.logging_utils import setup_logging, log_action, log_error

logger = setup_logging()


class LinkedInMCPServer:
    """LinkedIn MCP Server - Handles real LinkedIn posting"""

    def __init__(self):
        """Initialize LinkedIn API client"""
        self.access_token = LINKEDIN_ACCESS_TOKEN
        self.page_id = LINKEDIN_PAGE_ID
        self.base_url = "https://api.linkedin.com/v2"
        self.authenticated = bool(self.access_token and self.page_id)

    def _get_headers(self) -> dict:
        """Get request headers with auth"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        }

    def post_to_page(
        self,
        text: str,
        image_url: str = None,
        video_url: str = None
    ) -> dict:
        """
        Post content to LinkedIn company page

        Args:
            text: Post text content
            image_url: Optional image URL to attach
            video_url: Optional video URL to attach

        Returns:
            Dict with status and post ID
        """
        try:
            if not self.authenticated:
                return {
                    "success": False,
                    "error": "LinkedIn not authenticated. Missing credentials."
                }

            # Build post content
            post_content = {
                "commentary": {
                    "text": text
                },
                "visibility": {
                    "com.linkedin.ugc.visibility.MemberNetworkVisibility": "PUBLIC"
                },
                "lifecycleState": "PUBLISHED",
                "distribution": {
                    "feedDistribution": "FOLLOWERS",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": []
                }
            }

            # Add media if provided
            if image_url or video_url:
                post_content["content"] = {
                    "media": {
                        "title": "Media Post",
                        "description": text[:200]
                    }
                }

            # Make request to LinkedIn API
            url = f"{self.base_url}/ugcPosts"
            headers = self._get_headers()

            # For company pages, add X-Requested-With header
            response = requests.post(
                url,
                json=post_content,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                post_id = response.json().get('id', 'unknown')
                logger.info(f"✅ LinkedIn post created: {post_id}")
                log_action(
                    "linkedin_post_created",
                    "linkedin",
                    "success",
                    {
                        "post_id": post_id,
                        "text_length": len(text),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return {
                    "success": True,
                    "post_id": post_id,
                    "text": text[:50] + "..." if len(text) > 50 else text
                }
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                logger.error(f"❌ LinkedIn API error: {error_msg}")
                log_error("linkedin_post_failed", error_msg, {"text": text[:100]})
                return {
                    "success": False,
                    "error": error_msg
                }

        except requests.RequestException as e:
            logger.error(f"❌ LinkedIn request failed: {e}")
            log_error("linkedin_request_failed", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Failed to post to LinkedIn: {e}")
            log_error("linkedin_post_failed", str(e))
            return {"success": False, "error": str(e)}

    def get_page_info(self) -> dict:
        """Get LinkedIn page info"""
        try:
            if not self.authenticated:
                return {"authenticated": False}

            headers = self._get_headers()
            url = f"{self.base_url}/organizationAcls"
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                return {
                    "authenticated": True,
                    "page_id": self.page_id,
                    "status": "connected"
                }
            return {"authenticated": False}
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return {"authenticated": False, "error": str(e)}


# Singleton instance
_linkedin_server = None


def get_linkedin_server() -> LinkedInMCPServer:
    """Get or create singleton LinkedIn server"""
    global _linkedin_server
    if _linkedin_server is None:
        _linkedin_server = LinkedInMCPServer()
    return _linkedin_server


def post_to_linkedin(text: str, image_url: str = None, video_url: str = None) -> dict:
    """Convenience function to post to LinkedIn"""
    server = get_linkedin_server()
    return server.post_to_page(text, image_url, video_url)
