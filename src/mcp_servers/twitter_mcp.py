"""Twitter/X MCP Server — exposes Twitter tools to Claude Code.

Tools available to Claude:
    - draft_tweet       : Create a tweet draft routed through HITL approval
    - schedule_tweet    : Queue a tweet from the Content Calendar for a given date/time
    - get_timeline      : Fetch recent tweets from the authenticated account's timeline
    - get_tweet_metrics : Fetch engagement metrics for a specific tweet ID
    - process_approved  : Publish all approved TWITTER_*.md files in /Approved/

SAFETY: draft_tweet and schedule_tweet NEVER publish directly. They create approval
files in /Pending_Approval/. Publishing only happens after a human moves the file
to /Approved/ (via process_approved or the orchestrator's watch loop).

Credentials (loaded from .env — NEVER committed to git):
    TWITTER_API_KEY              OAuth 1.0a consumer key
    TWITTER_API_SECRET           OAuth 1.0a consumer secret
    TWITTER_ACCESS_TOKEN         OAuth 1.0a access token
    TWITTER_ACCESS_TOKEN_SECRET  OAuth 1.0a access token secret
    TWITTER_BEARER_TOKEN         Bearer token (read-only timeline/metrics)
    TWITTER_DRY_RUN              "true" (default) to log only, "false" to publish

Setup:
    1. Add Twitter credentials to .env
    2. Register this server in .claude/mcp.json
    3. Verify: claude mcp list
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Paths — resolve relative to project root (two levels up from this file)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"
APPROVED = VAULT_PATH / "Approved"
DONE = VAULT_PATH / "Done"
CONTENT_CALENDAR = VAULT_PATH / "Business" / "Content_Calendar.md"

TWEET_MAX_CHARS = 280

mcp = FastMCP("zoya-twitter")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_env() -> dict[str, str]:
    """Load Twitter credentials from .env without importing src.config
    (keeps the MCP server self-contained for subprocess isolation)."""
    from dotenv import load_dotenv
    import os

    load_dotenv(PROJECT_ROOT / ".env")
    return {
        "api_key": os.getenv("TWITTER_API_KEY", ""),
        "api_secret": os.getenv("TWITTER_API_SECRET", ""),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN", ""),
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
        "bearer_token": os.getenv("TWITTER_BEARER_TOKEN", ""),
        "dry_run": os.getenv("TWITTER_DRY_RUN", "true").lower() == "true",
    }


def _tweepy_client():
    """Return an authenticated tweepy.Client (API v2)."""
    try:
        import tweepy  # type: ignore
    except ImportError:
        raise RuntimeError("tweepy not installed. Run: uv add tweepy")

    creds = _load_env()
    if not all([creds["api_key"], creds["api_secret"],
                creds["access_token"], creds["access_token_secret"]]):
        raise RuntimeError(
            "Twitter OAuth credentials incomplete. "
            "Set TWITTER_API_KEY, TWITTER_API_SECRET, "
            "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET in .env"
        )

    return tweepy.Client(
        bearer_token=creds["bearer_token"] or None,
        consumer_key=creds["api_key"],
        consumer_secret=creds["api_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"],
    )


def _write_approval_file(
    tweet_text: str,
    hashtags: str,
    source_ref: str,
    scheduled_for: str,
) -> Path:
    """Create a TWITTER_*.md approval file in /Pending_Approval/."""
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    approval_file = PENDING_APPROVAL / f"TWITTER_{timestamp}.md"

    full_text = tweet_text.rstrip()
    if hashtags:
        full_text = f"{full_text}\n\n{hashtags}"

    creds = _load_env()
    approval_file.write_text(
        f"---\n"
        f"type: twitter_post\n"
        f"source_ref: {source_ref}\n"
        f"created_at: {now.isoformat()}\n"
        f"scheduled_for: {scheduled_for}\n"
        f"approval_required: true\n"
        f"status: pending_approval\n"
        f"platform: twitter\n"
        f"dry_run: {'true' if creds['dry_run'] else 'false'}\n"
        f"char_count: {len(full_text)}\n"
        f"---\n\n"
        f"## Draft Tweet\n\n"
        f"{full_text}\n\n"
        f"## Hashtags\n\n"
        f"{hashtags}\n\n"
        f"## Notes for Reviewer\n\n"
        f"- Source: {source_ref or 'manual'}\n"
        f"- Scheduled for: {scheduled_for or 'ASAP'}\n"
        f"- Character count: {len(full_text)} / {TWEET_MAX_CHARS}\n"
        f"- DRY_RUN: {'enabled — will log only' if creds['dry_run'] else 'DISABLED — will publish live'}\n\n"
        f"Move this file to `/Approved/` to publish or `/Rejected/` to discard.\n",
        encoding="utf-8",
    )
    return approval_file


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def draft_tweet(
    content: str,
    hashtags: str = "",
    source_ref: str = "",
) -> str:
    """Create a tweet draft and route it through HITL approval.

    Does NOT post immediately. Creates a TWITTER_*.md file in /Pending_Approval/.
    A human must move the file to /Approved/ before it is published.

    Args:
        content: Tweet text (keep under 280 chars including hashtags).
        hashtags: Optional space-separated hashtags (e.g. '#AI #Productivity').
        source_ref: Reference to the source that inspired this tweet.

    Returns:
        Confirmation message with the approval file path.
    """
    full = content.rstrip()
    if hashtags:
        full = f"{full}\n\n{hashtags}"

    if len(full) > TWEET_MAX_CHARS:
        return (
            f"Tweet too long: {len(full)} chars (max {TWEET_MAX_CHARS}). "
            "Please shorten the content or remove some hashtags."
        )

    approval_file = _write_approval_file(
        tweet_text=content,
        hashtags=hashtags,
        source_ref=source_ref,
        scheduled_for="",
    )
    return (
        f"Tweet draft created and routed for approval: {approval_file.name}\n"
        f"Character count: {len(full)} / {TWEET_MAX_CHARS}\n"
        f"Move to /Approved/ in Obsidian to publish."
    )


@mcp.tool()
def schedule_tweet(
    content: str,
    scheduled_for: str,
    hashtags: str = "",
    source_ref: str = "",
) -> str:
    """Queue a tweet from the Content Calendar for a specific date/time.

    Creates a TWITTER_*.md file in /Pending_Approval/ tagged with a
    scheduled_for timestamp. The orchestrator or a human approves it
    before the scheduled time.

    Args:
        content: Tweet text (keep under 280 chars including hashtags).
        scheduled_for: ISO-8601 datetime string (e.g. '2026-02-25T09:00:00Z').
        hashtags: Optional space-separated hashtags.
        source_ref: Content Calendar entry or campaign name.

    Returns:
        Confirmation message with the approval file path.
    """
    full = content.rstrip()
    if hashtags:
        full = f"{full}\n\n{hashtags}"

    if len(full) > TWEET_MAX_CHARS:
        return (
            f"Tweet too long: {len(full)} chars (max {TWEET_MAX_CHARS}). "
            "Please shorten the content or remove some hashtags."
        )

    approval_file = _write_approval_file(
        tweet_text=content,
        hashtags=hashtags,
        source_ref=source_ref,
        scheduled_for=scheduled_for,
    )
    return (
        f"Tweet scheduled for {scheduled_for} and routed for approval: {approval_file.name}\n"
        f"Character count: {len(full)} / {TWEET_MAX_CHARS}\n"
        f"Move to /Approved/ in Obsidian to confirm scheduling."
    )


@mcp.tool()
def get_timeline(count: int = 10) -> str:
    """Fetch the most recent tweets from the authenticated account's timeline.

    Uses Twitter API v2 (read-only, requires TWITTER_BEARER_TOKEN or OAuth).

    Args:
        count: Number of recent tweets to return (1–100, default 10).

    Returns:
        Formatted markdown list of recent tweets.
    """
    count = max(1, min(count, 100))

    try:
        client = _tweepy_client()
        # get_home_timeline returns tweets from accounts the user follows
        response = client.get_home_timeline(
            max_results=count,
            tweet_fields=["created_at", "public_metrics", "author_id"],
            expansions=["author_id"],
            user_fields=["username"],
        )
    except Exception as exc:
        return f"Failed to fetch timeline: {exc}"

    if not response.data:
        return "No tweets found in timeline."

    # Build author map from includes
    author_map: dict[str, str] = {}
    if response.includes and "users" in response.includes:
        for user in response.includes["users"]:
            author_map[user.id] = user.username

    lines = [f"### Recent Timeline ({len(response.data)} tweets)\n"]
    for tweet in response.data:
        author = author_map.get(str(tweet.author_id), str(tweet.author_id))
        metrics = tweet.public_metrics or {}
        created = getattr(tweet, "created_at", "")
        lines.append(
            f"**@{author}** · {created}\n"
            f"{tweet.text}\n"
            f"Likes: {metrics.get('like_count', 0)} | "
            f"Retweets: {metrics.get('retweet_count', 0)} | "
            f"Replies: {metrics.get('reply_count', 0)}\n"
            f"---"
        )

    return "\n".join(lines)


@mcp.tool()
def get_tweet_metrics(tweet_id: str) -> str:
    """Fetch engagement metrics for a specific tweet.

    Args:
        tweet_id: The numeric tweet ID string (e.g. '1234567890').

    Returns:
        Formatted markdown with engagement metrics.
    """
    try:
        client = _tweepy_client()
        response = client.get_tweet(
            id=tweet_id,
            tweet_fields=["created_at", "public_metrics", "text"],
        )
    except Exception as exc:
        return f"Failed to fetch tweet metrics: {exc}"

    if not response.data:
        return f"Tweet {tweet_id} not found."

    tweet = response.data
    metrics = tweet.public_metrics or {}
    return (
        f"### Tweet Metrics: {tweet_id}\n\n"
        f"**Text:** {tweet.text}\n\n"
        f"**Created:** {getattr(tweet, 'created_at', 'unknown')}\n\n"
        f"| Metric | Count |\n"
        f"|--------|-------|\n"
        f"| Likes | {metrics.get('like_count', 0)} |\n"
        f"| Retweets | {metrics.get('retweet_count', 0)} |\n"
        f"| Replies | {metrics.get('reply_count', 0)} |\n"
        f"| Quotes | {metrics.get('quote_count', 0)} |\n"
        f"| Impressions | {metrics.get('impression_count', 0)} |\n"
    )


@mcp.tool()
def process_approved_tweets() -> str:
    """Publish all approved TWITTER_*.md files found in /Approved/.

    Reads each approved file, extracts the draft tweet, posts it via
    Twitter API v2 (or logs in DRY_RUN mode), then moves the file to /Done/.

    Returns:
        Summary of how many tweets were processed and their outcomes.
    """
    APPROVED.mkdir(parents=True, exist_ok=True)
    DONE.mkdir(parents=True, exist_ok=True)

    import shutil

    creds = _load_env()
    results: list[str] = []
    count = 0

    for md_file in sorted(APPROVED.glob("TWITTER_*.md")):
        raw = md_file.read_text(encoding="utf-8")

        # Extract ## Draft Tweet section
        tweet_text = ""
        in_draft = False
        for line in raw.splitlines():
            if line.strip() == "## Draft Tweet":
                in_draft = True
                continue
            if in_draft and line.startswith("## "):
                break
            if in_draft:
                tweet_text += line + "\n"

        tweet_text = tweet_text.strip()
        if not tweet_text:
            results.append(f"SKIP {md_file.name}: empty content")
            continue

        tweet_text = tweet_text[:TWEET_MAX_CHARS]
        success = False
        tweet_id = ""

        if creds["dry_run"]:
            success = True
            tweet_id = "DRY_RUN"
        else:
            try:
                client = _tweepy_client()
                response = client.create_tweet(text=tweet_text)
                tweet_id = response.data["id"]
                success = True
            except Exception as exc:
                results.append(f"FAIL {md_file.name}: {exc}")

        if success:
            dest = DONE / md_file.name
            shutil.move(str(md_file), dest)

            # Patch frontmatter status
            updated = raw.replace(
                "status: pending_approval",
                f"status: done\nposted: {'true' if not creds['dry_run'] else 'false (dry_run)'}\n"
                f"tweet_id: {tweet_id}\nprocessed_at: {datetime.now(timezone.utc).isoformat()}",
                1,
            )
            dest.write_text(updated, encoding="utf-8")
            results.append(
                f"OK {md_file.name}: tweet_id={tweet_id}"
                + (" [DRY RUN]" if creds["dry_run"] else "")
            )
            count += 1

    if not results:
        return "No approved TWITTER_*.md files found in /Approved/."

    summary = f"Processed {count} tweet(s):\n" + "\n".join(f"- {r}" for r in results)
    return summary


@mcp.tool()
def read_content_calendar() -> str:
    """Read the Content Calendar and return scheduled Twitter posts.

    Reads AI_Employee_Vault/Business/Content_Calendar.md and returns
    all entries tagged for Twitter/X so you can draft them.

    Returns:
        Markdown excerpt of Twitter-tagged calendar entries.
    """
    if not CONTENT_CALENDAR.exists():
        return (
            f"Content Calendar not found at {CONTENT_CALENDAR}. "
            "Create AI_Employee_Vault/Business/Content_Calendar.md to use this tool."
        )

    content = CONTENT_CALENDAR.read_text(encoding="utf-8")

    # Filter to lines/sections mentioning Twitter or X
    lines = content.splitlines()
    relevant: list[str] = []
    capture = False
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in ["twitter", "tweet", "x.com", "x post"]):
            capture = True
        if capture:
            relevant.append(line)
            # Stop capturing after a blank line following content
            if line.strip() == "" and relevant and relevant[-2].strip() != "":
                capture = False

    if not relevant:
        return "No Twitter/X entries found in Content_Calendar.md."

    return "### Twitter Entries from Content Calendar\n\n" + "\n".join(relevant)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the Twitter MCP server via stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
