"""
Meta MCP Server - Real Facebook & Instagram Posting Implementation
Uses Meta Graph API to post to Facebook and Instagram
"""

import requests
from datetime import datetime

from src.config import PROJECT_ROOT
from src.utils.logging_utils import setup_logging, log_action, log_error

logger = setup_logging()


class MetaMCPServer:
    """Meta MCP Server - Handles Facebook & Instagram posting"""

    def __init__(self):
        """Initialize Meta API client"""
        self.base_url = "https://graph.instagram.com/v18.0"
        self.facebook_url = "https://graph.facebook.com/v18.0"

        # Load Meta credentials from config
        self.meta_token = None
        self.instagram_id = None
        self.facebook_page_id = None

        self._load_credentials()
        self.authenticated = bool(self.meta_token)

    def _load_credentials(self):
        """Load Meta credentials from environment or file"""
        import os
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")

        self.meta_token = os.getenv("META_ACCESS_TOKEN", "")
        self.instagram_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
        self.facebook_page_id = os.getenv("FACEBOOK_PAGE_ID", "")

    def _get_headers(self) -> dict:
        """Get request headers with auth"""
        return {
            "Authorization": f"Bearer {self.meta_token}",
            "Content-Type": "application/json"
        }

    def post_to_instagram(
        self,
        caption: str,
        image_url: str = None,
        carousel_urls: list = None
    ) -> dict:
        """
        Post to Instagram Business Account

        Args:
            caption: Post caption
            image_url: Single image URL
            carousel_urls: List of image URLs for carousel

        Returns:
            Dict with status and post ID
        """
        try:
            if not self.authenticated or not self.instagram_id:
                return {
                    "success": False,
                    "error": "Instagram not authenticated"
                }

            # Create image container for single image
            if image_url:
                container_payload = {
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self.meta_token
                }

                url = f"{self.base_url}/{self.instagram_id}/media"
                response = requests.post(url, json=container_payload, timeout=10)

                if response.status_code in [200, 201]:
                    creation_id = response.json().get('id')

                    # Publish the container
                    publish_payload = {
                        "creation_id": creation_id,
                        "access_token": self.meta_token
                    }
                    publish_url = f"{self.base_url}/{self.instagram_id}/media_publish"
                    publish_response = requests.post(
                        publish_url,
                        json=publish_payload,
                        timeout=10
                    )

                    if publish_response.status_code in [200, 201]:
                        post_id = publish_response.json().get('id')
                        logger.info(f"✅ Instagram post created: {post_id}")
                        log_action(
                            "instagram_post",
                            "instagram",
                            "success",
                            {
                                "post_id": post_id,
                                "caption_length": len(caption),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                        )
                        return {
                            "success": True,
                            "post_id": post_id,
                            "caption": caption[:50] + "..." if len(caption) > 50 else caption
                        }

            return {
                "success": False,
                "error": "No image provided or API error"
            }

        except requests.RequestException as e:
            logger.error(f"❌ Instagram request failed: {e}")
            log_error("instagram_post_failed", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Failed to post to Instagram: {e}")
            log_error("instagram_failed", str(e))
            return {"success": False, "error": str(e)}

    def post_to_facebook(
        self,
        message: str,
        image_url: str = None,
        video_url: str = None
    ) -> dict:
        """
        Post to Facebook Page

        Args:
            message: Post message
            image_url: Optional image URL
            video_url: Optional video URL

        Returns:
            Dict with status and post ID
        """
        try:
            if not self.authenticated or not self.facebook_page_id:
                return {
                    "success": False,
                    "error": "Facebook not authenticated"
                }

            # Build post payload
            payload = {
                "message": message,
                "access_token": self.meta_token
            }

            if image_url:
                payload["picture"] = image_url
            if video_url:
                payload["video_url"] = video_url

            url = f"{self.facebook_url}/{self.facebook_page_id}/feed"
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code in [200, 201]:
                post_id = response.json().get('id')
                logger.info(f"✅ Facebook post created: {post_id}")
                log_action(
                    "facebook_post",
                    "facebook",
                    "success",
                    {
                        "post_id": post_id,
                        "message_length": len(message),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return {
                    "success": True,
                    "post_id": post_id,
                    "message": message[:50] + "..." if len(message) > 50 else message
                }
            else:
                error_msg = f"Status {response.status_code}: {response.text}"
                logger.error(f"❌ Facebook API error: {error_msg}")
                return {"success": False, "error": error_msg}

        except requests.RequestException as e:
            logger.error(f"❌ Facebook request failed: {e}")
            log_error("facebook_post_failed", str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Failed to post to Facebook: {e}")
            log_error("facebook_failed", str(e))
            return {"success": False, "error": str(e)}

    def get_page_info(self) -> dict:
        """Get Meta page info"""
        try:
            if not self.authenticated:
                return {"authenticated": False}

            return {
                "authenticated": True,
                "facebook_page_id": self.facebook_page_id,
                "instagram_id": self.instagram_id,
                "status": "connected"
            }
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return {"authenticated": False, "error": str(e)}


# Singleton instance
_meta_server = None


def get_meta_server() -> MetaMCPServer:
    """Get or create singleton Meta server"""
    global _meta_server
    if _meta_server is None:
        _meta_server = MetaMCPServer()
    return _meta_server


def post_to_instagram(caption: str, image_url: str = None) -> dict:
    """Convenience function to post to Instagram"""
    server = get_meta_server()
    return server.post_to_instagram(caption, image_url)


def post_to_facebook(message: str, image_url: str = None) -> dict:
    """Convenience function to post to Facebook"""
    server = get_meta_server()
    return server.post_to_facebook(message, image_url)
