"""
LinkedIn Watcher using Playwright

Monitors LinkedIn for:
- Unread DMs (direct messages)
- Comments on your posts
- Profile visitors

Features:
- Persistent browser session
- Anti-detection mechanisms (random delays, user agent)
- Human-in-the-Loop: creates action files for approval
- Separate check intervals for DMs, comments, visitors
- Safety limits: max 10 actions per day
- Only runs during configured hours (8 AM - 8 PM default)
"""

import json
import logging
import time
import random
from pathlib import Path
from datetime import datetime, time as datetime_time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from playwright.sync_api import sync_playwright, BrowserContext, Page
from base_watcher import BaseWatcher


@dataclass
class LinkedInDM:
    """Represents a LinkedIn direct message."""
    sender_name: str
    sender_title: str
    sender_company: str
    message_preview: str
    timestamp: str
    message_id: str  # Unique ID to prevent duplicates
    profile_url: str = ""


@dataclass
class LinkedInComment:
    """Represents a comment on your LinkedIn post."""
    commenter_name: str
    comment_text: str
    post_title: str
    timestamp: str
    message_id: str  # Unique ID to prevent duplicates
    profile_url: str = ""


@dataclass
class LinkedInVisitor:
    """Represents a profile visitor."""
    visitor_name: str
    job_title: str
    company: str
    industry: str
    visit_count: int = 1
    last_visited: str = ""


class LinkedInWatcher(BaseWatcher):
    """
    Monitor LinkedIn for DMs, comments, and profile visitors.

    Features:
    - Persistent session (login saved)
    - Anti-detection: random delays, user agent spoofing
    - Time-based operation: only runs during configured hours
    - Daily action limit: max 10 actions per day (safety)
    - Duplicate detection: tracks processed message IDs
    - Human-in-the-Loop: creates .md files for approval
    """

    LINKEDIN_URL = "https://www.linkedin.com"
    MESSAGES_URL = "https://www.linkedin.com/messaging/"
    NOTIFICATIONS_URL = "https://www.linkedin.com/notifications/"
    PROFILE_VIEWS_URL = "https://www.linkedin.com/me/profile-views/"
    FEED_URL = "https://www.linkedin.com/feed/"

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        check_interval_dm: int = 7200,  # 2 hours
        check_interval_comments: int = 10800,  # 3 hours
        check_interval_visitors: int = 86400,  # 24 hours
        max_daily_actions: int = 10,
        run_start_hour: int = 8,
        run_end_hour: int = 20,
        target_industries: List[str] = None,
        hashtags: str = "",
        user_agent: str = "",
        browser_headless: bool = True,
        browser_timeout: int = 60,
        log_level: str = "INFO",
        dry_run: bool = False,
        enable_anti_detection: bool = True
    ):
        """
        Initialize LinkedIn Watcher.

        Args:
            vault_path: Path to Obsidian vault
            session_path: Path to save browser session
            check_interval_dm: Seconds between DM checks (default: 2 hours)
            check_interval_comments: Seconds between comment checks (default: 3 hours)
            check_interval_visitors: Seconds between visitor checks (default: 24 hours)
            max_daily_actions: Max actions per day for safety (default: 10)
            run_start_hour: Hour to start operations (default: 8 AM)
            run_end_hour: Hour to end operations (default: 8 PM)
            target_industries: Industries for lead scoring
            hashtags: Default hashtags to use in posts
            user_agent: Custom user agent string
            browser_headless: Run browser in headless mode
            browser_timeout: Page load timeout in seconds
            log_level: Logging level
            dry_run: Test mode (log without acting)
            enable_anti_detection: Use anti-detection mechanisms
        """
        super().__init__(vault_path, check_interval=60, log_level=log_level)

        self.session_path = Path(session_path).resolve()
        self.check_interval_dm = check_interval_dm
        self.check_interval_comments = check_interval_comments
        self.check_interval_visitors = check_interval_visitors
        self.max_daily_actions = max_daily_actions
        self.run_start_hour = run_start_hour
        self.run_end_hour = run_end_hour
        self.target_industries = target_industries or []
        self.hashtags = hashtags
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.browser_headless = browser_headless
        self.browser_timeout = browser_timeout
        self.dry_run = dry_run
        self.enable_anti_detection = enable_anti_detection

        # Tracking
        self.processed_ids_file = Path("linkedin_processed.json")
        self.processed_ids = self._load_processed_ids()
        self.daily_action_count = 0
        self.last_dm_check = 0
        self.last_comment_check = 0
        self.last_visitor_check = 0

        # Create LinkedIn subfolder in vault
        self.linkedin_path = self.vault_path / "LinkedIn"
        self.linkedin_path.mkdir(parents=True, exist_ok=True)

        # Browser instance
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

        self.logger.info(f"LinkedIn Watcher initialized")
        self.logger.info(f"  Max daily actions: {self.max_daily_actions}")
        self.logger.info(f"  Operating hours: {self.run_start_hour}:00 - {self.run_end_hour}:00")
        self.logger.info(f"  Anti-detection: {self.enable_anti_detection}")

    def _load_processed_ids(self) -> set:
        """Load previously processed message IDs."""
        if self.processed_ids_file.exists():
            try:
                with open(self.processed_ids_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
            except Exception as e:
                self.logger.warning(f"Could not load processed IDs: {e}")
        return set()

    def _save_processed_ids(self) -> None:
        """Save processed message IDs to file."""
        try:
            with open(self.processed_ids_file, 'w') as f:
                json.dump({
                    'processed_ids': list(self.processed_ids),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save processed IDs: {e}")

    def _is_within_operating_hours(self) -> bool:
        """Check if current time is within operating hours."""
        current_hour = datetime.now().hour
        return self.run_start_hour <= current_hour < self.run_end_hour

    def _should_skip_due_to_limits(self) -> bool:
        """Check if we should skip due to daily action limit."""
        if self.daily_action_count >= self.max_daily_actions:
            self.logger.warning(
                f"Daily action limit reached ({self.daily_action_count}/{self.max_daily_actions})"
            )
            return True
        return False

    def _random_delay(self, min_sec: float = 2.0, max_sec: float = 5.0) -> None:
        """Apply random delay for anti-detection."""
        if self.enable_anti_detection:
            delay = random.uniform(min_sec, max_sec)
            time.sleep(delay)

    def _init_browser(self) -> None:
        """Initialize Playwright browser with persistent context."""
        if self.browser is not None:
            return

        try:
            self.logger.debug("Initializing Playwright browser...")
            self.playwright = sync_playwright().start()

            # Create session directory
            self.session_path.mkdir(parents=True, exist_ok=True)

            # Launch browser
            self.browser = self.playwright.chromium.launch(
                headless=self.browser_headless
            )

            # Create context with custom user agent and stored session
            context_args = {
                "user_agent": self.user_agent
            }

            # Load existing session if available
            session_state_file = self.session_path / "state.json"
            if session_state_file.exists():
                try:
                    with open(session_state_file, 'r') as f:
                        context_args['storage_state'] = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load session state: {e}")

            self.context = self.browser.new_context(**context_args)
            self.page = self.context.new_page()
            self.page.set_default_timeout(self.browser_timeout * 1000)

            self.logger.info("Browser initialized with custom user agent and saved session")

        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            self._cleanup_browser()
            raise

    def _cleanup_browser(self) -> None:
        """Cleanup browser resources."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                # Save session state
                try:
                    state = self.context.storage_state()
                    self.session_path.mkdir(parents=True, exist_ok=True)
                    with open(self.session_path / "state.json", 'w') as f:
                        json.dump(state, f)
                except Exception as e:
                    self.logger.warning(f"Could not save session state: {e}")
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Error during browser cleanup: {e}")
        finally:
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Main check method (called by base watcher).

        Returns list of updates (DMs, comments, etc).
        Base watcher will call create_action_file for each update.
        """
        updates = []

        # Check if within operating hours
        if not self._is_within_operating_hours():
            return updates

        # Check if daily limit reached
        if self._should_skip_due_to_limits():
            return updates

        try:
            # Initialize browser if needed
            if self.browser is None:
                self._init_browser()

            current_time = time.time()

            # Check DMs
            if current_time - self.last_dm_check >= self.check_interval_dm:
                dms = self._check_dms()
                updates.extend([{"type": "dm", "data": dm} for dm in dms])
                self.last_dm_check = current_time

            # Check comments
            if current_time - self.last_comment_check >= self.check_interval_comments:
                comments = self._check_comments()
                updates.extend([{"type": "comment", "data": comment} for comment in comments])
                self.last_comment_check = current_time

            # Check profile visitors (only for Premium users, we have free account)
            # Still check but with reduced frequency for free accounts
            if current_time - self.last_visitor_check >= self.check_interval_visitors:
                visitors = self._check_profile_visitors()
                updates.extend([{"type": "visitor", "data": visitor} for visitor in visitors])
                self.last_visitor_check = current_time

            # Update processed IDs
            if updates:
                self._save_processed_ids()

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}", exc_info=True)

        return updates

    def _check_dms(self) -> List[LinkedInDM]:
        """Check for unread direct messages."""
        dms = []

        try:
            self.logger.debug("Checking for unread DMs...")
            self._random_delay()

            self.page.goto(self.MESSAGES_URL, wait_until="networkidle", timeout=30000)
            self._random_delay(3.0, 7.0)

            # Wait for messaging interface to load
            try:
                self.page.wait_for_selector('[data-test-id="message-list"]', timeout=self.browser_timeout * 1000)
            except Exception as e:
                self.logger.warning(f"Message list did not load: {e}")
                return dms

            # Find unread message threads
            # LinkedIn indicates unread with specific styling/badges
            unread_threads = self.page.query_selector_all('[data-test-id="message-item"][data-unread="true"]')

            self.logger.debug(f"Found {len(unread_threads)} unread message threads")

            for thread in unread_threads:
                try:
                    # Extract sender info
                    sender_name_elem = thread.query_selector('[data-test-id="message-sender-name"]')
                    if not sender_name_elem:
                        continue

                    sender_name = sender_name_elem.inner_text().strip()

                    # Get message preview
                    preview_elem = thread.query_selector('[data-test-id="message-preview"]')
                    message_preview = preview_elem.inner_text().strip() if preview_elem else ""

                    # Get timestamp
                    time_elem = thread.query_selector('[data-test-id="message-time"]')
                    timestamp = time_elem.get_attribute('data-time') or datetime.now().isoformat()

                    # Create unique ID
                    message_id = f"dm_{sender_name}_{timestamp}_{hash(message_preview) & 0x7fffffff}"

                    # Skip if already processed
                    if message_id in self.processed_ids:
                        continue

                    # Click to get full info
                    thread.click()
                    self._random_delay(1.0, 2.0)

                    # Get sender title and company (in profile preview)
                    sender_title = "Unknown Title"
                    sender_company = "Unknown Company"

                    try:
                        title_elem = self.page.query_selector('[data-test-id="sender-title"]')
                        if title_elem:
                            sender_title = title_elem.inner_text().strip()

                        company_elem = self.page.query_selector('[data-test-id="sender-company"]')
                        if company_elem:
                            sender_company = company_elem.inner_text().strip()
                    except:
                        pass

                    # Create DM object
                    dm = LinkedInDM(
                        sender_name=sender_name,
                        sender_title=sender_title,
                        sender_company=sender_company,
                        message_preview=message_preview,
                        timestamp=timestamp,
                        message_id=message_id
                    )

                    dms.append(dm)
                    self.processed_ids.add(message_id)
                    self.daily_action_count += 1

                    self.logger.info(f"Found DM from {sender_name}")

                except Exception as e:
                    self.logger.debug(f"Error processing DM thread: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking DMs: {e}", exc_info=True)

        return dms

    def _check_comments(self) -> List[LinkedInComment]:
        """Check for comments on your posts."""
        comments = []

        try:
            self.logger.debug("Checking for new comments...")
            self._random_delay()

            self.page.goto(self.NOTIFICATIONS_URL, wait_until="networkidle", timeout=30000)
            self._random_delay(3.0, 7.0)

            # Wait for notifications to load
            try:
                self.page.wait_for_selector('[data-test-id="notification-list"]', timeout=self.browser_timeout * 1000)
            except:
                self.logger.warning("Notification list did not load")
                return comments

            # Find comment notifications
            comment_notifications = self.page.query_selector_all(
                '[data-test-id="notification-item"][data-notification-type="comment"]'
            )

            self.logger.debug(f"Found {len(comment_notifications)} comment notifications")

            for notif in comment_notifications:
                try:
                    # Extract commenter name
                    commenter_elem = notif.query_selector('[data-test-id="commenter-name"]')
                    if not commenter_elem:
                        continue

                    commenter_name = commenter_elem.inner_text().strip()

                    # Get comment text
                    comment_elem = notif.query_selector('[data-test-id="comment-text"]')
                    comment_text = comment_elem.inner_text().strip() if comment_elem else ""

                    # Get post title
                    post_elem = notif.query_selector('[data-test-id="post-title"]')
                    post_title = post_elem.inner_text().strip() if post_elem else "Unknown Post"

                    # Get timestamp
                    time_elem = notif.query_selector('[data-test-id="notification-time"]')
                    timestamp = time_elem.get_attribute('data-time') or datetime.now().isoformat()

                    # Create unique ID
                    message_id = f"comment_{commenter_name}_{timestamp}_{hash(comment_text) & 0x7fffffff}"

                    # Skip if already processed
                    if message_id in self.processed_ids:
                        continue

                    # Create comment object
                    comment = LinkedInComment(
                        commenter_name=commenter_name,
                        comment_text=comment_text,
                        post_title=post_title,
                        timestamp=timestamp,
                        message_id=message_id
                    )

                    comments.append(comment)
                    self.processed_ids.add(message_id)
                    self.daily_action_count += 1

                    self.logger.info(f"Found comment from {commenter_name} on post: {post_title}")

                except Exception as e:
                    self.logger.debug(f"Error processing comment notification: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking comments: {e}", exc_info=True)

        return comments

    def _check_profile_visitors(self) -> List[LinkedInVisitor]:
        """Check profile visitors (limited on free account)."""
        visitors = []

        try:
            self.logger.debug("Checking for profile visitors...")
            self._random_delay()

            self.page.goto(self.PROFILE_VIEWS_URL, wait_until="networkidle", timeout=30000)
            self._random_delay(3.0, 7.0)

            # Wait for visitors list to load
            try:
                self.page.wait_for_selector('[data-test-id="visitor-list"]', timeout=self.browser_timeout * 1000)
            except:
                self.logger.warning("Visitor list did not load (may need Premium)")
                return visitors

            # Find visitor items
            visitor_items = self.page.query_selector_all('[data-test-id="visitor-item"]')

            self.logger.debug(f"Found {len(visitor_items)} profile visitors")

            for item in visitor_items[:10]:  # Limit to first 10 for free account
                try:
                    # Extract visitor name
                    name_elem = item.query_selector('[data-test-id="visitor-name"]')
                    if not name_elem:
                        continue

                    visitor_name = name_elem.inner_text().strip()

                    # Get job title
                    title_elem = item.query_selector('[data-test-id="visitor-title"]')
                    job_title = title_elem.inner_text().strip() if title_elem else "Unknown"

                    # Get company
                    company_elem = item.query_selector('[data-test-id="visitor-company"]')
                    company = company_elem.inner_text().strip() if company_elem else "Unknown"

                    # Get industry
                    industry_elem = item.query_selector('[data-test-id="visitor-industry"]')
                    industry = industry_elem.inner_text().strip() if industry_elem else "Unknown"

                    visitor = LinkedInVisitor(
                        visitor_name=visitor_name,
                        job_title=job_title,
                        company=company,
                        industry=industry,
                        last_visited=datetime.now().isoformat()
                    )

                    visitors.append(visitor)
                    self.logger.info(f"Found profile visitor: {visitor_name} from {company}")

                except Exception as e:
                    self.logger.debug(f"Error processing visitor: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking profile visitors: {e}", exc_info=True)

        return visitors

    def create_action_file(self, update: Dict[str, Any]) -> None:
        """
        Create markdown action file from update.

        Args:
            update: Update dict with 'type' and 'data' keys
        """
        try:
            update_type = update.get('type')
            data = update.get('data')

            if update_type == 'dm':
                self._create_dm_file(data)
            elif update_type == 'comment':
                self._create_comment_file(data)
            elif update_type == 'visitor':
                self._create_visitor_report(data)

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}", exc_info=True)

    def _create_dm_file(self, dm: LinkedInDM) -> None:
        """Create action file for a DM."""
        try:
            msg_time = datetime.fromisoformat(dm.timestamp)
            filename = f"LINKEDIN_DM_{msg_time.strftime('%Y%m%d_%H%M%S')}_{dm.sender_name.replace(' ', '_')}.md"
            filepath = self.needs_action_path / filename

            content = f"""---
type: linkedin_dm
from: {dm.sender_name}
from_title: {dm.sender_title}
from_company: {dm.sender_company}
received: {dm.timestamp}
priority: high
status: pending
approval_required: true
---

## LinkedIn Direct Message

**From:** {dm.sender_name}
**Title:** {dm.sender_title}
**Company:** {dm.sender_company}
**Received:** {msg_time.strftime('%Y-%m-%d %H:%M %p')}

### Message Preview
"{dm.message_preview}"

## Suggested Actions
- [ ] Read full message on LinkedIn
- [ ] Reply to {dm.sender_name}
- [ ] Add to contacts/CRM
- [ ] Schedule follow-up
- [ ] Mark as done

## Draft Reply
*(Claude will compose this)*

---
*Created by LinkedIn Watcher v1.0 at {datetime.now().isoformat()}*
"""

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would create: {filepath}")
            else:
                filepath.write_text(content, encoding='utf-8')
                self.logger.info(f"Created DM action file: {filepath}")

        except Exception as e:
            self.logger.error(f"Error creating DM file: {e}", exc_info=True)

    def _create_comment_file(self, comment: LinkedInComment) -> None:
        """Create action file for a comment."""
        try:
            msg_time = datetime.fromisoformat(comment.timestamp)
            filename = f"LINKEDIN_COMMENT_{msg_time.strftime('%Y%m%d_%H%M%S')}_{comment.commenter_name.replace(' ', '_')}.md"
            filepath = self.needs_action_path / filename

            content = f"""---
type: linkedin_comment
from: {comment.commenter_name}
on_post: {comment.post_title}
received: {comment.timestamp}
status: pending
approval_required: false
---

## New Comment on Your Post

**Commenter:** {comment.commenter_name}
**On Post:** "{comment.post_title}"
**Received:** {msg_time.strftime('%Y-%m-%d %H:%M %p')}

### Comment
"{comment.comment_text}"

## Suggested Actions
- [ ] Reply to comment
- [ ] Like the comment
- [ ] Send commenter a DM
- [ ] Mark as done

## Draft Reply
*(Claude will compose this)*

---
*Created by LinkedIn Watcher v1.0 at {datetime.now().isoformat()}*
"""

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would create: {filepath}")
            else:
                filepath.write_text(content, encoding='utf-8')
                self.logger.info(f"Created comment action file: {filepath}")

        except Exception as e:
            self.logger.error(f"Error creating comment file: {e}", exc_info=True)

    def _create_visitor_report(self, visitor: LinkedInVisitor) -> None:
        """Add visitor to weekly report."""
        # Visitors are accumulated in memory and written to weekly report
        # by weekly_linkedin_report.py
        self.logger.debug(f"Recorded visitor: {visitor.visitor_name}")

    def stop(self) -> None:
        """Stop the watcher and cleanup resources."""
        super().stop()
        self._cleanup_browser()


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./AI_Employee_Vault")
    session_path = os.getenv("LINKEDIN_SESSION_PATH", "./linkedin_session")
    check_interval_dm = int(os.getenv("LINKEDIN_CHECK_INTERVAL_DM", "7200"))
    check_interval_comments = int(os.getenv("LINKEDIN_CHECK_INTERVAL_COMMENTS", "10800"))
    check_interval_visitors = int(os.getenv("LINKEDIN_CHECK_INTERVAL_VISITORS", "86400"))
    max_daily_actions = int(os.getenv("LINKEDIN_MAX_DAILY_ACTIONS", "10"))
    run_start_hour = int(os.getenv("LINKEDIN_RUN_START_HOUR", "8"))
    run_end_hour = int(os.getenv("LINKEDIN_RUN_END_HOUR", "20"))
    target_industries = os.getenv("LINKEDIN_TARGET_INDUSTRIES", "").split(",")
    hashtags = os.getenv("LINKEDIN_HASHTAGS", "")
    user_agent = os.getenv("LINKEDIN_USER_AGENT", "")
    browser_headless = os.getenv("LINKEDIN_BROWSER_HEADLESS", "true").lower() == "true"
    browser_timeout = int(os.getenv("LINKEDIN_BROWSER_TIMEOUT", "60"))
    log_level = os.getenv("LINKEDIN_LOG_LEVEL", "INFO")
    dry_run = os.getenv("LINKEDIN_DRY_RUN", "false").lower() == "true"
    enable_anti_detection = os.getenv("LINKEDIN_ENABLE_ANTI_DETECTION", "true").lower() == "true"

    watcher = LinkedInWatcher(
        vault_path=vault_path,
        session_path=session_path,
        check_interval_dm=check_interval_dm,
        check_interval_comments=check_interval_comments,
        check_interval_visitors=check_interval_visitors,
        max_daily_actions=max_daily_actions,
        run_start_hour=run_start_hour,
        run_end_hour=run_end_hour,
        target_industries=target_industries,
        hashtags=hashtags,
        user_agent=user_agent,
        browser_headless=browser_headless,
        browser_timeout=browser_timeout,
        log_level=log_level,
        dry_run=dry_run,
        enable_anti_detection=enable_anti_detection
    )

    watcher.run()
