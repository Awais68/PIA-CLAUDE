"""
Twitter/X MCP Server - Real Tweet Posting Implementation
Uses Tweepy + Twitter API v2 to post actual tweets
"""

import tweepy
from datetime import datetime

from src.config import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET
)
from src.utils.logging_utils import setup_logging, log_action, log_error

logger = setup_logging()


class TwitterMCPServer:
    """Twitter MCP Server - Handles real tweet posting"""

    def __init__(self):
        """Initialize Twitter API v2 client"""
        self.client = None
        self.authenticated = False
        self._authenticate()

    def _authenticate(self) -> bool:
        """
        Authenticate with Twitter API v2

        Returns:
            True if authenticated successfully
        """
        try:
            if not all([TWITTER_API_KEY, TWITTER_API_SECRET,
                       TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
                logger.warning("⚠️ Twitter credentials incomplete in config")
                return False

            # Create Tweepy client with OAuth 1.0a
            self.client = tweepy.Client(
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True
            )

            # Verify authentication
            me = self.client.get_me()
            if me and me.data:
                self.authenticated = True
                logger.info(f"✅ Twitter authenticated as @{me.data.username}")
                log_action("twitter_authenticated", me.data.username, "success")
                return True
            else:
                logger.error("❌ Twitter authentication failed: Could not verify user")
                return False

        except tweepy.TweepyException as e:
            logger.error(f"❌ Twitter authentication error: {e}")
            log_error("twitter_auth_failed", str(e))
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize Twitter client: {e}")
            log_error("twitter_init_failed", str(e))
            return False

    def post_tweet(
        self,
        text: str,
        reply_to_id: str = None,
        quote_tweet_id: str = None
    ) -> dict:
        """
        Post a tweet to Twitter/X

        Args:
            text: Tweet text (max 280 characters)
            reply_to_id: Optional tweet ID to reply to
            quote_tweet_id: Optional tweet ID to quote

        Returns:
            Dict with status and tweet ID
        """
        try:
            if not self.authenticated:
                if not self._authenticate():
                    return {
                        "success": False,
                        "error": "Not authenticated"
                    }

            # Validate tweet length
            if len(text) > 280:
                logger.warning(f"⚠️ Tweet exceeds 280 chars: {len(text)} chars")
                text = text[:277] + "..."

            # Post tweet
            kwargs = {"text": text}
            if reply_to_id:
                kwargs["reply_settings"] = "public"
                kwargs["in_reply_to_tweet_id"] = reply_to_id
            if quote_tweet_id:
                kwargs["quote_tweet_id"] = quote_tweet_id

            response = self.client.create_tweet(**kwargs)

            if response and response.data:
                tweet_id = response.data['id']
                logger.info(f"✅ Tweet posted: {tweet_id}")
                log_action(
                    "tweet_posted",
                    "twitter",
                    "success",
                    {
                        "tweet_id": tweet_id,
                        "text_length": len(text),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return {
                    "success": True,
                    "tweet_id": tweet_id,
                    "text": text[:50] + "..." if len(text) > 50 else text
                }
            else:
                logger.error("❌ Tweet posting returned empty response")
                return {"success": False, "error": "Empty response"}

        except tweepy.TweepyException as e:
            logger.error(f"❌ Twitter API error: {e}")
            log_error("tweet_post_failed", str(e), {"text": text[:100]})
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Failed to post tweet: {e}")
            log_error("tweet_failed", str(e))
            return {"success": False, "error": str(e)}

    def get_user_info(self) -> dict:
        """Get authenticated user info"""
        try:
            if not self.client:
                return {"authenticated": False}

            me = self.client.get_me()
            if me and me.data:
                return {
                    "authenticated": True,
                    "username": me.data.username,
                    "id": me.data.id,
                    "name": me.data.name
                }
            return {"authenticated": False}
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return {"authenticated": False, "error": str(e)}


# Singleton instance
_twitter_server = None


def get_twitter_server() -> TwitterMCPServer:
    """Get or create singleton Twitter server"""
    global _twitter_server
    if _twitter_server is None:
        _twitter_server = TwitterMCPServer()
    return _twitter_server


def post_tweet(text: str) -> dict:
    """Convenience function to post tweet"""
    server = get_twitter_server()
    return server.post_tweet(text)
