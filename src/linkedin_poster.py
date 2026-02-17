"""LinkedIn Auto-Poster — generates and posts LinkedIn content.

Silver Tier Requirement: S3 (Automatically post on LinkedIn about business)

Flow:
    1. Generate post content based on recent activity or business context
    2. Create approval request in /Pending_Approval/ (HITL required)
    3. When human moves file to /Approved/, post to LinkedIn
    4. DRY_RUN mode logs the post without actually publishing

SAFETY: All posts go through HITL approval. Never auto-publish.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.config import (
    APPROVED,
    DONE,
    LINKEDIN_ACCESS_TOKEN,
    LINKEDIN_DRY_RUN,
    LINKEDIN_PAGE_ID,
    PENDING_APPROVAL,
)
from src.utils import log_action, setup_logger

logger = setup_logger("linkedin_poster")

LINKEDIN_API_URL = "https://api.linkedin.com/v2/ugcPosts"


def generate_post_content(topic: str, context: str = "") -> str:
    """Generate a LinkedIn post draft.

    In a full implementation, this would use Claude to generate content.
    For now, it creates a structured template.

    Args:
        topic: What the post is about.
        context: Additional context or source material.

    Returns:
        Draft post text.
    """
    post = (
        f"{topic}\n\n"
        f"{context}\n\n" if context else f"{topic}\n\n"
    )
    # Trim to LinkedIn optimal length
    return post[:1300]


def create_approval_request(post_content: str, hashtags: str = "", source_ref: str = "") -> Path:
    """Create an approval file in Pending_Approval for a LinkedIn post.

    Args:
        post_content: The draft post text.
        hashtags: Space-separated hashtags.
        source_ref: Reference to the source document that inspired the post.

    Returns:
        Path to the created approval file.
    """
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    approval_file = PENDING_APPROVAL / f"LINKEDIN_{timestamp}.md"
    approval_file.write_text(
        f"---\n"
        f"type: linkedin_post\n"
        f"source_ref: {source_ref}\n"
        f"created_at: {now.isoformat()}\n"
        f"approval_required: true\n"
        f"status: pending_approval\n"
        f"platform: linkedin\n"
        f"dry_run: {'true' if LINKEDIN_DRY_RUN else 'false'}\n"
        f"---\n\n"
        f"## Draft Post\n{post_content}\n\n"
        f"## Hashtags\n{hashtags}\n\n"
        f"## Notes for Reviewer\n"
        f"- Source: {source_ref or 'manual'}\n"
        f"- DRY_RUN: {'enabled' if LINKEDIN_DRY_RUN else 'disabled'}\n"
        f"- Move to /Approved/ to publish, /Rejected/ to discard.\n",
        encoding="utf-8",
    )
    log_action("linkedin_draft_created", str(approval_file), {"source": source_ref})
    logger.info("LinkedIn draft created: %s", approval_file.name)
    return approval_file


def post_to_linkedin(content: str) -> bool:
    """Post content to LinkedIn via API.

    If LINKEDIN_DRY_RUN is True, logs the post without publishing.

    Args:
        content: The post text to publish.

    Returns:
        True if posted (or dry-run logged), False on error.
    """
    if LINKEDIN_DRY_RUN:
        logger.info("[DRY RUN] Would post to LinkedIn:\n%s", content[:200])
        log_action("linkedin_post_dry_run", content[:100])
        return True

    if not LINKEDIN_ACCESS_TOKEN:
        logger.error("LINKEDIN_ACCESS_TOKEN not set. Cannot post.")
        return False

    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Build UGC post payload
    author = f"urn:li:organization:{LINKEDIN_PAGE_ID}" if LINKEDIN_PAGE_ID else "urn:li:person:me"
    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        response = requests.post(LINKEDIN_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code in (200, 201):
            logger.info("Posted to LinkedIn successfully")
            log_action("linkedin_posted", content[:100])
            return True
        else:
            logger.error("LinkedIn API error %d: %s", response.status_code, response.text[:300])
            return False
    except Exception:
        logger.exception("Failed to post to LinkedIn")
        return False


def process_approved_posts() -> int:
    """Check Approved/ for LinkedIn posts and publish them.

    Returns count of posts processed.
    """
    APPROVED.mkdir(parents=True, exist_ok=True)
    count = 0

    for md_file in sorted(APPROVED.glob("LINKEDIN_*.md")):
        content = md_file.read_text(encoding="utf-8")

        # Extract the draft post section
        post_text = ""
        in_draft = False
        for line in content.splitlines():
            if line.strip() == "## Draft Post":
                in_draft = True
                continue
            if in_draft and line.startswith("## "):
                break
            if in_draft:
                post_text += line + "\n"

        post_text = post_text.strip()
        if not post_text:
            logger.warning("Empty post content in %s, skipping", md_file.name)
            continue

        success = post_to_linkedin(post_text)

        # Move to Done regardless
        import shutil
        dest = DONE / md_file.name
        shutil.move(str(md_file), dest)

        from src.orchestrator import _update_frontmatter
        _update_frontmatter(dest, {
            "status": "done",
            "posted": "true" if success else "false",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })

        log_action("linkedin_post_processed", str(dest), {"success": success})
        count += 1

    return count


def main() -> None:
    """Entry point for LinkedIn poster."""
    logger.info("LinkedIn Poster — DRY_RUN=%s", LINKEDIN_DRY_RUN)

    # Process any approved posts
    count = process_approved_posts()
    if count > 0:
        logger.info("Processed %d approved LinkedIn post(s)", count)
    else:
        logger.info("No approved LinkedIn posts to process")


if __name__ == "__main__":
    main()
