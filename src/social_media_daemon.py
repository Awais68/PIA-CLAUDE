"""Social Media Daemon — Continuous monitoring for Twitter & LinkedIn posting.

This daemon runs continuously and:
1. Monitors Tweet_Queue.md for scheduled tweets
2. Creates approval requests when scheduled time arrives
3. Monitors /Approved/ folder and posts approved content to both platforms
4. Runs every 5 minutes

Usage: uv run zoya-social-daemon
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from pathlib import Path

from src.config import VAULT_PATH
from src.linkedin_poster import process_approved_posts as process_approved_linkedin_posts
from src.twitter_poster import create_approval_request, process_approved_tweets
from src.utils import setup_logger

logger = setup_logger("social_daemon")

TWEET_QUEUE_FILE = VAULT_PATH / "Business" / "Tweet_Queue.md"
CHECK_INTERVAL = 300  # 5 minutes


def parse_scheduled_tweets() -> list[dict]:
    """Parse Tweet_Queue.md and extract scheduled tweets.
    
    Returns list of dicts with: {scheduled_for, content, line_num, is_checked}
    """
    if not TWEET_QUEUE_FILE.exists():
        logger.warning("Tweet Queue file not found: %s", TWEET_QUEUE_FILE)
        return []

    content = TWEET_QUEUE_FILE.read_text(encoding="utf-8")
    scheduled_tweets = []
    
    # Pattern: - [ ] scheduled_for: YYYY-MM-DD HH:MM UTC | Tweet content here
    pattern = r'^- \[(?P<checked>[ x])\] scheduled_for:\s*(?P<datetime>[\d\-]+\s+[\d:]+)\s+UTC\s*\|\s*(?P<content>.+)$'
    
    for line_num, line in enumerate(content.splitlines(), 1):
        match = re.match(pattern, line.strip())
        if match:
            try:
                dt_str = match.group('datetime')
                scheduled_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                scheduled_dt = scheduled_dt.replace(tzinfo=timezone.utc)
                
                scheduled_tweets.append({
                    'scheduled_for': scheduled_dt,
                    'content': match.group('content').strip(),
                    'line_num': line_num,
                    'is_checked': match.group('checked') == 'x',
                    'original_line': line,
                })
            except ValueError as e:
                logger.warning("Failed to parse datetime in line %d: %s", line_num, e)
    
    return scheduled_tweets


def mark_tweet_as_processed(line_num: int) -> None:
    """Mark a tweet as processed by changing [ ] to [x] in Tweet_Queue.md."""
    if not TWEET_QUEUE_FILE.exists():
        return
    
    lines = TWEET_QUEUE_FILE.read_text(encoding="utf-8").splitlines()
    
    if 0 < line_num <= len(lines):
        # Change - [ ] to - [x]
        lines[line_num - 1] = lines[line_num - 1].replace('- [ ]', '- [x]', 1)
        
        TWEET_QUEUE_FILE.write_text('\n'.join(lines) + '\n', encoding="utf-8")
        logger.info("Marked tweet at line %d as processed", line_num)


def process_scheduled_tweets() -> int:
    """Check for tweets that should be posted now and create approval requests.
    
    Returns count of approval requests created.
    """
    scheduled = parse_scheduled_tweets()
    now = datetime.now(timezone.utc)
    count = 0
    
    for tweet in scheduled:
        # Skip if already processed
        if tweet['is_checked']:
            continue
        
        # Check if scheduled time has arrived
        if tweet['scheduled_for'] <= now:
            logger.info(
                "Creating approval for scheduled tweet: %s (scheduled for %s)",
                tweet['content'][:50],
                tweet['scheduled_for'].isoformat(),
            )
            
            # Create approval request
            create_approval_request(
                tweet_content=tweet['content'],
                source_ref=f"Tweet_Queue.md:L{tweet['line_num']}",
            )
            
            # Mark as processed in the queue file
            mark_tweet_as_processed(tweet['line_num'])
            count += 1
    
    return count


def run_daemon() -> None:
    """Main daemon loop."""
    logger.info("Social Media Daemon starting (interval: %ds)", CHECK_INTERVAL)
    logger.info("Monitoring: %s", TWEET_QUEUE_FILE)
    logger.info("Press Ctrl+C to stop")
    
    cycle = 0
    
    try:
        while True:
            cycle += 1
            logger.info("=== Cycle %d — %s ===", cycle, datetime.now(timezone.utc).isoformat())
            
            # 1. Process scheduled tweets from queue
            try:
                scheduled_count = process_scheduled_tweets()
                if scheduled_count > 0:
                    logger.info("Created %d approval request(s) from scheduled tweets", scheduled_count)
            except Exception as e:
                logger.exception("Error processing scheduled tweets: %s", e)
            
            # 2. Post approved Twitter content
            try:
                twitter_count = process_approved_tweets()
                if twitter_count > 0:
                    logger.info("Posted %d approved tweet(s)", twitter_count)
            except Exception as e:
                logger.exception("Error posting approved tweets: %s", e)
            
            # 3. Post approved LinkedIn content
            try:
                linkedin_count = process_approved_linkedin_posts()
                if linkedin_count > 0:
                    logger.info("Posted %d approved LinkedIn post(s)", linkedin_count)
            except Exception as e:
                logger.exception("Error posting approved LinkedIn posts: %s", e)
            
            logger.info("Cycle complete. Sleeping for %ds...", CHECK_INTERVAL)
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Social Media Daemon stopped by user")


def main() -> None:
    """Entry point for social media daemon."""
    run_daemon()


if __name__ == "__main__":
    main()
