"""Twitter Watcher — monitors mentions and processes the tweet queue every 30 min.

Silver/Gold Tier Requirement: Social media monitoring watcher.

Flow:
    1. Poll Twitter API v2 for recent brand/keyword mentions (last 30 min window)
    2. Classify mention urgency; write high-priority ones to /Needs_Action/
    3. Read AI_Employee_Vault/Business/Tweet_Queue.md and send due tweets to approval
    4. On Mondays: generate weekly Twitter analytics → /Briefings/

SAFETY: All outbound tweets go through HITL approval via create_approval_request().
        Nothing is posted directly from this watcher.

Credentials (set in .env — NEVER committed to git):
    TWITTER_API_KEY            OAuth 1.0a consumer key
    TWITTER_API_SECRET         OAuth 1.0a consumer secret
    TWITTER_ACCESS_TOKEN       OAuth 1.0a access token
    TWITTER_ACCESS_TOKEN_SECRET OAuth 1.0a access token secret
    TWITTER_BEARER_TOKEN       App-only bearer token (for search)
    TWITTER_DRY_RUN            "true" (default) skips API calls

Dependencies:
    uv add tweepy
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import (
    BRIEFINGS,
    NEEDS_ACTION,
    PENDING_APPROVAL,
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_DRY_RUN,
    VAULT_PATH,
)
from src.twitter_poster import create_approval_request
from src.utils import log_action, setup_logger
from src.watchers.base_watcher import BaseWatcher

logger = setup_logger("watcher.twitter")

# ---------------------------------------------------------------------------
# Configuration — edit to match your brand
# ---------------------------------------------------------------------------

BRAND_KEYWORDS: list[str] = [
    "YourBrandName",  # TODO: replace with your actual brand name
    "@YourHandle",    # TODO: replace with your Twitter handle
]

COMPETITOR_KEYWORDS: list[str] = [
    # "CompetitorA",  # TODO: add competitor names
]

INDUSTRY_KEYWORDS: list[str] = [
    "AI employee",
    "personal AI",
    "AI automation",
    "Claude Code",
]

TWEET_QUEUE_FILE = VAULT_PATH / "Business" / "Tweet_Queue.md"

# Mentions containing these terms are flagged high urgency
URGENT_TERMS = frozenset([
    "urgent", "asap", "broken", "bug", "lawsuit", "refund",
    "scam", "fraud", "error", "help", "issue", "problem",
])

BEARER_TOKEN_ENV = "TWITTER_BEARER_TOKEN"

# ---------------------------------------------------------------------------
# TwitterWatcher
# ---------------------------------------------------------------------------


class TwitterWatcher(BaseWatcher):
    """Polls Twitter API v2 every 30 minutes for mentions and queued tweets."""

    name = "twitter"

    def __init__(self) -> None:
        # 1800 seconds = 30 minutes
        super().__init__(poll_interval=1800, max_retries=3)
        self._client = None
        self._last_mention_check: datetime = datetime.now(timezone.utc) - timedelta(minutes=30)
        self._weekly_done_this_monday = False

    # ------------------------------------------------------------------
    # BaseWatcher interface
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """Authenticate with Twitter API v2."""
        NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
        PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
        BRIEFINGS.mkdir(parents=True, exist_ok=True)

        if TWITTER_DRY_RUN:
            logger.info("Twitter watcher running in DRY_RUN mode — no API calls")
            return

        if not TWITTER_API_KEY:
            logger.warning("TWITTER_API_KEY not set — Twitter watcher will skip API calls")
            return

        try:
            import tweepy  # type: ignore
            import os

            bearer = os.getenv(BEARER_TOKEN_ENV, "")
            self._client = tweepy.Client(
                bearer_token=bearer or None,
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True,
            )
            logger.info("Twitter API client initialised")
        except ImportError:
            logger.error("tweepy not installed — run: uv add tweepy")
        except Exception as exc:
            logger.error("Failed to init Twitter client: %s", exc)

    def poll(self) -> int:
        """One 30-minute cycle: check mentions + process queue. Returns items handled."""
        count = 0
        count += self._check_mentions()
        count += self._process_tweet_queue()
        count += self._maybe_weekly_analytics()
        self._last_mention_check = datetime.now(timezone.utc)
        return count

    def teardown(self) -> None:
        logger.info("Twitter watcher shutting down")

    # ------------------------------------------------------------------
    # Phase 1 — Mention monitoring
    # ------------------------------------------------------------------

    def _check_mentions(self) -> int:
        """Search for recent brand mentions; save urgent ones to /Needs_Action/."""
        if TWITTER_DRY_RUN or self._client is None:
            logger.debug("Skipping mention check (DRY_RUN or no client)")
            return 0

        all_keywords = BRAND_KEYWORDS + COMPETITOR_KEYWORDS + INDUSTRY_KEYWORDS
        if not all_keywords:
            return 0

        # Twitter search query — join keywords with OR
        query = " OR ".join(f'"{kw}"' for kw in all_keywords if kw.strip())
        # Exclude our own tweets to avoid self-loops
        if BRAND_KEYWORDS:
            own_handle = BRAND_KEYWORDS[0].lstrip("@")
            query += f" -from:{own_handle}"

        since = self._last_mention_check.strftime("%Y-%m-%dT%H:%M:%SZ")
        count = 0

        try:
            import tweepy  # type: ignore

            response = self._client.search_recent_tweets(
                query=query,
                max_results=50,
                start_time=since,
                tweet_fields=["created_at", "author_id", "text"],
                expansions=["author_id"],
                user_fields=["username"],
            )

            if not response.data:
                return 0

            # Build author_id → username map
            users = {u.id: u.username for u in (response.includes or {}).get("users", [])}

            for tweet in response.data:
                author = users.get(tweet.author_id, str(tweet.author_id))
                urgency = self._classify_urgency(tweet.text, author)

                if urgency == "high":
                    self._save_urgent_mention(tweet, author, urgency)
                    count += 1
                else:
                    logger.info(
                        "Mention (%s) from @%s: %s",
                        urgency, author, tweet.text[:80],
                    )

        except tweepy.TooManyRequests:
            logger.warning("Twitter rate limit hit — skipping this cycle")
        except Exception as exc:
            logger.error("Mention check failed: %s", exc)

        return count

    def _classify_urgency(self, text: str, author: str) -> str:
        """Return 'high', 'medium', or 'low' based on tweet content."""
        lower = text.lower()
        if any(term in lower for term in URGENT_TERMS):
            return "high"
        # Direct mention of our handle with a question mark
        if any(kw.lower() in lower for kw in BRAND_KEYWORDS) and "?" in text:
            return "high"
        if any(kw.lower() in lower for kw in BRAND_KEYWORDS):
            return "medium"
        return "low"

    def _save_urgent_mention(self, tweet, author: str, urgency: str) -> Path:
        """Write a high-urgency mention to /Needs_Action/ for orchestrator pickup."""
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        filename = NEEDS_ACTION / f"TWITTER_MENTION_{ts}_{author[:12]}.md"

        tweet_url = f"https://twitter.com/{author}/status/{tweet.id}"
        content = (
            f"---\n"
            f"type: twitter_mention\n"
            f"source: twitter\n"
            f"urgency: {urgency}\n"
            f"tweet_id: {tweet.id}\n"
            f"author: @{author}\n"
            f"received_at: {now.isoformat()}\n"
            f"status: pending\n"
            f"priority: high\n"
            f"---\n\n"
            f"## Urgent Twitter Mention\n\n"
            f"**Author:** @{author}\n"
            f"**URL:** {tweet_url}\n"
            f"**Received:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            f"### Tweet\n\n"
            f"{tweet.text}\n\n"
            f"## Why Urgent\n"
            f"Tweet matched urgency criteria (keywords: {', '.join(URGENT_TERMS & set(tweet.text.lower().split()))}).\n\n"
            f"## Suggested Actions\n"
            f"- [ ] Review the mention\n"
            f"- [ ] Draft a reply via the twitter-agent skill\n"
            f"- [ ] Escalate to human if legal/PR issue\n"
        )
        filename.write_text(content, encoding="utf-8")
        log_action("twitter_urgent_mention", str(filename), {"author": author, "tweet_id": str(tweet.id)})
        logger.info("Saved urgent mention from @%s → %s", author, filename.name)
        return filename

    # ------------------------------------------------------------------
    # Phase 2 — Tweet queue processing
    # ------------------------------------------------------------------

    def _process_tweet_queue(self) -> int:
        """Read Tweet_Queue.md and send any due tweets to Pending_Approval/."""
        if not TWEET_QUEUE_FILE.exists():
            logger.debug("Tweet_Queue.md not found — skipping queue processing")
            return 0

        raw = TWEET_QUEUE_FILE.read_text(encoding="utf-8")
        now = datetime.now(timezone.utc)
        count = 0
        updated_lines: list[str] = []

        for line in raw.splitlines():
            matched = re.match(
                r"^- \[ \] scheduled_for:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+UTC\s+\|\s+(.+)$",
                line,
            )
            if matched:
                raw_dt, tweet_text = matched.group(1), matched.group(2).strip()
                try:
                    scheduled_dt = datetime.strptime(raw_dt, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                except ValueError:
                    updated_lines.append(line)
                    continue

                if scheduled_dt <= now:
                    # Extract hashtags from text
                    hashtags = " ".join(w for w in tweet_text.split() if w.startswith("#"))
                    tweet_body = " ".join(w for w in tweet_text.split() if not w.startswith("#"))

                    create_approval_request(
                        tweet_content=tweet_body,
                        hashtags=hashtags,
                        source_ref="Tweet_Queue.md",
                    )
                    stamp = now.strftime("%Y-%m-%d %H:%M")
                    updated_lines.append(f"- [x] (sent to approval {stamp}) {tweet_text}")
                    logger.info("Tweet queued for approval: %s…", tweet_text[:60])
                    count += 1
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        if count > 0:
            TWEET_QUEUE_FILE.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
            log_action("twitter_queue_processed", str(TWEET_QUEUE_FILE), {"sent_to_approval": count})

        return count

    # ------------------------------------------------------------------
    # Phase 3 — Weekly analytics
    # ------------------------------------------------------------------

    def _maybe_weekly_analytics(self) -> int:
        """Generate weekly analytics report on Mondays. Returns 1 if generated."""
        now = datetime.now(timezone.utc)
        is_monday = now.weekday() == 0
        is_morning = now.hour == 8

        # Only generate once per Monday (track via flag; resets on process restart)
        if not (is_monday and is_morning):
            return 0
        if self._weekly_done_this_monday:
            return 0

        self._weekly_done_this_monday = True
        self._generate_weekly_analytics(now)
        return 1

    def _generate_weekly_analytics(self, now: datetime) -> Path:
        """Produce a Twitter analytics briefing document."""
        week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        week_end = now.strftime("%Y-%m-%d")
        ts = now.strftime("%Y%m%d_%H%M%S")
        out_file = BRIEFINGS / f"TWITTER_ANALYTICS_{ts}.md"

        if TWITTER_DRY_RUN or self._client is None:
            # Produce a stub report in dry-run mode
            metrics = {
                "followers": "N/A (DRY_RUN)",
                "impressions": "N/A (DRY_RUN)",
                "engagements": "N/A (DRY_RUN)",
            }
            top_tweets: list[str] = ["(DRY_RUN — no live data)"]
        else:
            metrics, top_tweets = self._fetch_analytics_data(now)

        content = (
            f"---\n"
            f"type: twitter_analytics\n"
            f"period: weekly\n"
            f"generated_at: {now.isoformat()}\n"
            f"covers_from: {week_start}\n"
            f"covers_to: {week_end}\n"
            f"---\n\n"
            f"# Twitter Weekly Analytics — Week of {week_start}\n\n"
            f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"## Follower Summary\n\n"
            f"| Metric | Value |\n"
            f"|--------|-------|\n"
            f"| Followers (end of week) | {metrics.get('followers', 'N/A')} |\n"
            f"| New followers this week | {metrics.get('new_followers', 'N/A')} |\n\n"
            f"## Engagement\n\n"
            f"| Metric | Count |\n"
            f"|--------|-------|\n"
            f"| Total impressions | {metrics.get('impressions', 'N/A')} |\n"
            f"| Total engagements | {metrics.get('engagements', 'N/A')} |\n"
            f"| Avg. engagement rate | {metrics.get('engagement_rate', 'N/A')} |\n\n"
            f"## Top Tweets This Week\n\n"
        )
        for i, t in enumerate(top_tweets[:3], 1):
            content += f"{i}. {t}\n"

        content += (
            f"\n## Monitored Keywords\n\n"
            f"| Keyword | Mentions |\n"
            f"|---------|----------|\n"
        )
        for kw in BRAND_KEYWORDS + INDUSTRY_KEYWORDS:
            content += f"| {kw} | {metrics.get(f'kw_{kw}', 'N/A')} |\n"

        content += (
            f"\n## Recommendations\n\n"
            f"- [ ] Review top-performing tweet and consider a follow-up thread\n"
            f"- [ ] Reply to any unanswered mentions from the week\n"
            f"- [ ] Schedule next week's tweets in Tweet_Queue.md\n"
        )

        BRIEFINGS.mkdir(parents=True, exist_ok=True)
        out_file.write_text(content, encoding="utf-8")
        log_action("twitter_analytics_generated", str(out_file), {"week": week_start})
        logger.info("Twitter analytics saved: %s", out_file.name)
        return out_file

    def _fetch_analytics_data(self, now: datetime) -> tuple[dict, list[str]]:
        """Fetch real metrics from Twitter API v2. Returns (metrics_dict, top_tweets)."""
        metrics: dict = {}
        top_tweets: list[str] = []

        try:
            import tweepy  # type: ignore

            # Get authenticated user info
            me = self._client.get_me(user_fields=["public_metrics"])
            if me.data:
                pub = me.data.public_metrics or {}
                metrics["followers"] = pub.get("followers_count", "N/A")

            # Search own tweets from the last 7 days for engagement data
            week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
            my_tweets = self._client.search_recent_tweets(
                query=f"from:{BRAND_KEYWORDS[0].lstrip('@') if BRAND_KEYWORDS else 'me'}",
                max_results=100,
                start_time=week_ago,
                tweet_fields=["public_metrics", "text"],
            )

            total_impressions = 0
            total_engagements = 0
            tweet_perf: list[tuple[int, str]] = []

            for tw in (my_tweets.data or []):
                pm = tw.public_metrics or {}
                impressions = pm.get("impression_count", 0)
                engagements = (
                    pm.get("like_count", 0)
                    + pm.get("retweet_count", 0)
                    + pm.get("reply_count", 0)
                )
                total_impressions += impressions
                total_engagements += engagements
                tweet_perf.append((engagements, tw.text[:100]))

            metrics["impressions"] = total_impressions
            metrics["engagements"] = total_engagements
            if total_impressions > 0:
                rate = round(total_engagements / total_impressions * 100, 2)
                metrics["engagement_rate"] = f"{rate}%"

            tweet_perf.sort(reverse=True)
            top_tweets = [f'"{text}" — {eng} engagements' for eng, text in tweet_perf[:3]]

        except Exception as exc:
            logger.error("Failed to fetch analytics: %s", exc)
            metrics["error"] = str(exc)

        return metrics, top_tweets


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the Twitter watcher (runs indefinitely, polls every 30 min)."""
    watcher = TwitterWatcher()
    watcher.start()


if __name__ == "__main__":
    main()
