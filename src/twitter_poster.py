"""Twitter / X Auto-Poster — generates and posts tweets with HITL approval.

Flow:
    1. Generate tweet content based on recent activity or a given topic
    2. Create approval request in /Pending_Approval/ (human-in-the-loop required)
    3. When human moves file to /Approved/, post to Twitter via API v2
    4. TWITTER_DRY_RUN mode logs the tweet without publishing

SAFETY: All tweets go through HITL approval. Never auto-publish.

Credentials (loaded from .env — NEVER committed to git):
    TWITTER_API_KEY            OAuth 1.0a consumer key
    TWITTER_API_SECRET         OAuth 1.0a consumer secret
    TWITTER_ACCESS_TOKEN       OAuth 1.0a access token
    TWITTER_ACCESS_TOKEN_SECRET OAuth 1.0a access token secret
    TWITTER_DRY_RUN            "true" (default) to log only, "false" to publish

Dependencies:
    uv add tweepy
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from src.config import (
    APPROVED,
    DONE,
    PENDING_APPROVAL,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_DRY_RUN,
)
from src.utils import log_action, setup_logger

logger = setup_logger("twitter_poster")

TWEET_MAX_CHARS = 280


def create_approval_request(
    tweet_content: str,
    hashtags: str = "",
    source_ref: str = "",
) -> Path:
    """Save a tweet draft to Pending_Approval/ for human review.

    Args:
        tweet_content: Draft tweet text (will be trimmed to 280 chars at post time).
        hashtags: Space-separated hashtags to append (optional).
        source_ref: Reference to source document that inspired the tweet.

    Returns:
        Path to the created approval file.
    """
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    approval_file = PENDING_APPROVAL / f"TWITTER_{timestamp}.md"

    full_text = tweet_content
    if hashtags:
        full_text = f"{tweet_content.rstrip()}\n\n{hashtags}"

    approval_file.write_text(
        f"---\n"
        f"type: twitter_post\n"
        f"source_ref: {source_ref}\n"
        f"created_at: {now.isoformat()}\n"
        f"approval_required: true\n"
        f"status: pending_approval\n"
        f"platform: twitter\n"
        f"dry_run: {'true' if TWITTER_DRY_RUN else 'false'}\n"
        f"char_count: {len(full_text)}\n"
        f"---\n\n"
        f"## Draft Tweet\n{full_text}\n\n"
        f"## Hashtags\n{hashtags}\n\n"
        f"## Notes for Reviewer\n"
        f"- Source: {source_ref or 'manual'}\n"
        f"- Character count: {len(full_text)} / {TWEET_MAX_CHARS}\n"
        f"- DRY_RUN: {'enabled' if TWITTER_DRY_RUN else 'disabled'}\n"
        f"- Move to /Approved/ to publish, /Rejected/ to discard.\n",
        encoding="utf-8",
    )
    log_action("twitter_draft_created", str(approval_file), {"source": source_ref})
    logger.info("Twitter draft created: %s", approval_file.name)
    return approval_file


def post_tweet(content: str) -> bool:
    """Post a tweet via Twitter API v2.

    If TWITTER_DRY_RUN is True, logs without publishing.

    Args:
        content: Tweet text (truncated to 280 chars if necessary).

    Returns:
        True if posted (or dry-run), False on error.
    """
    content = content[:TWEET_MAX_CHARS]

    if TWITTER_DRY_RUN:
        logger.info("[DRY RUN] Would tweet:\n%s", content)
        log_action("twitter_post_dry_run", content[:100])
        return True

    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        logger.error("Twitter credentials incomplete — cannot post. Check .env file.")
        return False

    try:
        import tweepy  # type: ignore

        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        )
        response = client.create_tweet(text=content)
        tweet_id = response.data["id"]
        logger.info("Tweet posted successfully (id=%s)", tweet_id)
        log_action("twitter_posted", content[:100], {"tweet_id": tweet_id})
        return True

    except Exception:
        logger.exception("Failed to post tweet")
        return False


def process_approved_tweets() -> int:
    """Check Approved/ for TWITTER_*.md files and publish them.

    Returns count of tweets processed.
    """
    APPROVED.mkdir(parents=True, exist_ok=True)
    count = 0

    for md_file in sorted(APPROVED.glob("TWITTER_*.md")):
        text = md_file.read_text(encoding="utf-8")

        # Extract the draft tweet section
        tweet_text = ""
        in_draft = False
        for line in text.splitlines():
            if line.strip() == "## Draft Tweet":
                in_draft = True
                continue
            if in_draft and line.startswith("## "):
                break
            if in_draft:
                tweet_text += line + "\n"

        tweet_text = tweet_text.strip()
        if not tweet_text:
            logger.warning("Empty tweet content in %s, skipping", md_file.name)
            continue

        success = post_tweet(tweet_text)

        dest = DONE / md_file.name
        shutil.move(str(md_file), dest)

        # Update frontmatter
        from src.orchestrator import _update_frontmatter
        _update_frontmatter(dest, {
            "status": "done",
            "posted": "true" if success else "false",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })

        log_action("twitter_post_processed", str(dest), {"success": success})
        logger.info("Twitter post processed: %s (success=%s)", md_file.name, success)
        count += 1

    return count


def main() -> None:
    """Entry point for Twitter poster."""
    logger.info("Twitter Poster — DRY_RUN=%s", TWITTER_DRY_RUN)
    count = process_approved_tweets()
    if count > 0:
        logger.info("Processed %d approved tweet(s)", count)
    else:
        logger.info("No approved tweets to process")


if __name__ == "__main__":
    main()
