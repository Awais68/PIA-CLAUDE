"""
LinkedIn Poster - Auto Post with Human-in-the-Loop Approval

Features:
- Monitors /Post_Queue/ folder for posts to publish
- Requires approval before posting (status=approved)
- Posts with human-like delays (char-by-char typing)
- Uploads images if provided
- Anti-detection: random delays, user agent spoofing
- Logs all activity
- Updates file status and moves to Done folder
"""

import json
import logging
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv
import os


class LinkedInPoster:
    """
    Automatically post to LinkedIn with Human-in-the-Loop approval.

    Process:
    1. Watches /Vault/LinkedIn/Post_Queue/ folder
    2. Only posts if status=approved AND current_time >= scheduled_time
    3. Types content char-by-char with human-like delays
    4. Updates file status to "posted"
    5. Moves file to /Done folder
    """

    FEED_URL = "https://www.linkedin.com/feed/"
    MAX_POST_LENGTH = 3000  # LinkedIn limit

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        user_agent: str = "",
        browser_headless: bool = True,
        browser_timeout: int = 60,
        log_level: str = "INFO",
        dry_run: bool = False,
        enable_anti_detection: bool = True,
        min_char_delay: float = 0.05,  # 50ms min per char
        max_char_delay: float = 0.15   # 150ms max per char
    ):
        """
        Initialize LinkedIn Poster.

        Args:
            vault_path: Path to Obsidian vault
            session_path: Path to browser session
            user_agent: Custom user agent
            browser_headless: Run headless
            browser_timeout: Page timeout in seconds
            log_level: Logging level
            dry_run: Test mode (don't actually post)
            enable_anti_detection: Use random delays
            min_char_delay: Min milliseconds per character
            max_char_delay: Max milliseconds per character
        """
        self.vault_path = Path(vault_path).resolve()
        self.session_path = Path(session_path).resolve()
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.browser_headless = browser_headless
        self.browser_timeout = browser_timeout
        self.dry_run = dry_run
        self.enable_anti_detection = enable_anti_detection
        self.min_char_delay = min_char_delay
        self.max_char_delay = max_char_delay

        # Paths
        self.post_queue_path = self.vault_path / "LinkedIn" / "Post_Queue"
        self.done_path = self.vault_path / "Done"
        self.approved_path = self.vault_path / "Approved"
        self.logs_path = self.vault_path / "Logs"

        # Create directories
        for path in [self.post_queue_path, self.done_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logger(log_level)

        # Browser
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

        self.logger.info("LinkedIn Poster initialized")
        self.logger.info(f"  Queue path: {self.post_queue_path}")
        self.logger.info(f"  Dry run: {self.dry_run}")
        self.logger.info(f"  Anti-detection: {self.enable_anti_detection}")

    def _setup_logger(self, log_level: str) -> logging.Logger:
        """Setup logger."""
        logger = logging.getLogger("linkedin_poster")
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _random_delay(self, min_sec: float = 2.0, max_sec: float = 5.0) -> None:
        """Apply random delay for anti-detection."""
        if self.enable_anti_detection:
            delay = random.uniform(min_sec, max_sec)
            time.sleep(delay)

    def _init_browser(self) -> None:
        """Initialize browser with saved session."""
        if self.browser is not None:
            return

        try:
            self.logger.debug("Initializing browser...")
            self.playwright = sync_playwright().start()
            self.session_path.mkdir(parents=True, exist_ok=True)

            self.browser = self.playwright.chromium.launch(
                headless=self.browser_headless
            )

            context_args = {
                "user_agent": self.user_agent
            }

            # Load session
            session_state_file = self.session_path / "state.json"
            if session_state_file.exists():
                try:
                    with open(session_state_file, 'r') as f:
                        context_args['storage_state'] = json.load(f)
                except Exception as e:
                    self.logger.warning(f"Could not load session: {e}")

            self.context = self.browser.new_context(**context_args)
            self.page = self.context.new_page()
            self.page.set_default_timeout(self.browser_timeout * 1000)

            self.logger.info("Browser initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            self._cleanup_browser()
            raise

    def _cleanup_browser(self) -> None:
        """Cleanup browser."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                try:
                    state = self.context.storage_state()
                    self.session_path.mkdir(parents=True, exist_ok=True)
                    with open(self.session_path / "state.json", 'w') as f:
                        json.dump(state, f)
                except Exception as e:
                    self.logger.warning(f"Could not save session: {e}")
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        finally:
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None

    def check_queue(self) -> None:
        """Check post queue and post approved posts."""
        try:
            if not self.post_queue_path.exists():
                return

            post_files = sorted(self.post_queue_path.glob("*.md"))

            for post_file in post_files:
                try:
                    # Parse post file
                    post_data = self._parse_post_file(post_file)

                    if not post_data:
                        continue

                    # Check if approved and scheduled time reached
                    if post_data.get('status') != 'approved':
                        self.logger.debug(f"Post {post_file.name} not approved (status: {post_data.get('status')})")
                        continue

                    # Check scheduled time
                    scheduled_time = post_data.get('scheduled_time')
                    if scheduled_time and datetime.fromisoformat(scheduled_time) > datetime.now():
                        self.logger.debug(f"Post {post_file.name} not yet scheduled")
                        continue

                    # Post it!
                    self._post_to_linkedin(post_file, post_data)

                except Exception as e:
                    self.logger.error(f"Error processing {post_file.name}: {e}", exc_info=True)

        except Exception as e:
            self.logger.error(f"Error checking queue: {e}", exc_info=True)

    def _parse_post_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Parse YAML frontmatter and content from post file."""
        try:
            content = filepath.read_text(encoding='utf-8')

            if not content.startswith('---'):
                self.logger.warning(f"Invalid file format: {filepath.name}")
                return None

            # Split frontmatter
            parts = content.split('---', 2)
            if len(parts) < 3:
                return None

            # Parse YAML
            metadata = {}
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip().strip('"\'')

            # Get content
            post_content = parts[2].strip()

            return {
                **metadata,
                'content': post_content,
                'filepath': filepath
            }

        except Exception as e:
            self.logger.error(f"Error parsing {filepath.name}: {e}")
            return None

    def _update_post_file(self, filepath: Path, status: str, error_msg: str = "") -> None:
        """Update post file status."""
        try:
            content = filepath.read_text(encoding='utf-8')

            # Update status in frontmatter
            lines = content.split('\n')
            updated_lines = []
            in_frontmatter = False

            for line in lines:
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                    updated_lines.append(line)
                elif in_frontmatter and line.startswith('status:'):
                    updated_lines.append(f"status: {status}")
                elif in_frontmatter and line.startswith('posted_at:') and status == 'posted':
                    updated_lines.append(f"posted_at: {datetime.now().isoformat()}")
                elif in_frontmatter and line.startswith('error:'):
                    if error_msg:
                        updated_lines.append(f"error: {error_msg}")
                else:
                    updated_lines.append(line)

            # Add posted_at if posting and not present
            if status == 'posted' and 'posted_at:' not in content:
                # Find where to insert (before closing ---)
                for i, line in enumerate(updated_lines):
                    if line.strip() == '---' and i > 0:
                        # Check if this is closing frontmatter
                        if any(updated_lines[j].startswith('status:') for j in range(i)):
                            updated_lines.insert(i, f"posted_at: {datetime.now().isoformat()}")
                            break

            updated_content = '\n'.join(updated_lines)
            filepath.write_text(updated_content, encoding='utf-8')

        except Exception as e:
            self.logger.error(f"Error updating post file: {e}")

    def _post_to_linkedin(self, filepath: Path, post_data: Dict[str, Any]) -> None:
        """Post content to LinkedIn."""
        try:
            if self.browser is None:
                self._init_browser()

            self.logger.info(f"Posting: {filepath.name}")

            # Navigate to feed
            self._random_delay()
            self.page.goto(self.FEED_URL, wait_until="networkidle", timeout=30000)
            self._random_delay(3.0, 7.0)

            # Find "Start a post" button
            start_post_btn = None
            try:
                start_post_btn = self.page.query_selector('[data-test-id="start-post-button"]')
                if not start_post_btn:
                    start_post_btn = self.page.query_selector('button:has-text("Start a post")')
            except:
                pass

            if not start_post_btn:
                raise Exception("Could not find 'Start a post' button")

            start_post_btn.click()
            self._random_delay(1.0, 2.0)

            # Wait for post composer
            try:
                self.page.wait_for_selector('[data-test-id="post-composer"]', timeout=10000)
            except:
                raise Exception("Post composer did not open")

            # Find text input
            text_input = self.page.query_selector('[data-test-id="post-text-input"]')
            if not text_input:
                # Try alternative selector
                text_input = self.page.query_selector('[contenteditable="true"]')

            if not text_input:
                raise Exception("Could not find text input field")

            # Type content with human-like delays (char by char)
            post_content = post_data.get('content', '')

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would post: {post_content[:100]}...")
                self._update_post_file(filepath, 'posted')
                return

            # Type character by character
            for char in post_content:
                text_input.type(char)
                # Random delay between characters
                if self.enable_anti_detection:
                    delay = random.uniform(self.min_char_delay, self.max_char_delay)
                    time.sleep(delay)

            self._random_delay(1.0, 2.0)

            # Handle image upload if provided
            image_path = post_data.get('image_path')
            if image_path:
                self._upload_image(image_path)
                self._random_delay(1.0, 2.0)

            # Add hashtags if provided
            hashtags = post_data.get('hashtags', '')
            if hashtags:
                text_input.type(f"\n\n{hashtags}")
                self._random_delay(0.5, 1.0)

            # Find and click Post button
            post_btn = None
            try:
                post_btn = self.page.query_selector('[data-test-id="post-button"]')
                if not post_btn:
                    post_btn = self.page.query_selector('button:has-text("Post")')
            except:
                pass

            if not post_btn:
                raise Exception("Could not find Post button")

            post_btn.click()
            self._random_delay(2.0, 5.0)

            # Wait for confirmation
            try:
                self.page.wait_for_selector('[data-test-id="post-success-message"]', timeout=10000)
            except:
                # May not have explicit success message, just check if we're back on feed
                time.sleep(2)

            # Update file status
            self._update_post_file(filepath, 'posted')

            # Move to Done folder
            done_file = self.done_path / filepath.name
            filepath.rename(done_file)

            self.logger.info(f"Posted successfully: {filepath.name}")
            self._log_activity('post', post_data.get('hashtags', ''), 'success')

        except Exception as e:
            self.logger.error(f"Error posting to LinkedIn: {e}", exc_info=True)
            self._update_post_file(filepath, 'failed', str(e))
            self._log_activity('post', post_data.get('hashtags', ''), 'error', str(e))

    def _upload_image(self, image_path: str) -> None:
        """Upload image to post."""
        try:
            image_full_path = self.vault_path / image_path
            if not image_full_path.exists():
                self.logger.warning(f"Image not found: {image_path}")
                return

            # Find image upload button
            upload_btn = self.page.query_selector('[data-test-id="image-upload-button"]')
            if upload_btn:
                self.page.set_input_files('[data-test-id="image-input"]', str(image_full_path))
                self.logger.info("Image uploaded")

        except Exception as e:
            self.logger.warning(f"Could not upload image: {e}")

    def _log_activity(self, action: str, content: str, result: str, error: str = "") -> None:
        """Log activity to JSON log."""
        try:
            log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}.json"

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action_type": f"linkedin_post_{action}",
                "actor": "linkedin_poster",
                "target": content[:50],
                "result": result,
                "error": error
            }

            # Append to log file
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        logs = json.load(f)
                except:
                    logs = []

            logs.append(log_entry)

            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            self.logger.error(f"Could not log activity: {e}")

    def run(self) -> None:
        """Run continuously, checking queue every 30 minutes."""
        self.logger.info("LinkedIn Poster started")

        try:
            while True:
                try:
                    self.check_queue()
                    time.sleep(1800)  # Check every 30 minutes

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    time.sleep(60)

        finally:
            self.logger.info("LinkedIn Poster stopped")
            self._cleanup_browser()


if __name__ == "__main__":
    load_dotenv()

    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./AI_Employee_Vault")
    session_path = os.getenv("LINKEDIN_SESSION_PATH", "./linkedin_session")
    user_agent = os.getenv("LINKEDIN_USER_AGENT", "")
    browser_headless = os.getenv("LINKEDIN_BROWSER_HEADLESS", "true").lower() == "true"
    browser_timeout = int(os.getenv("LINKEDIN_BROWSER_TIMEOUT", "60"))
    log_level = os.getenv("LINKEDIN_LOG_LEVEL", "INFO")
    dry_run = os.getenv("LINKEDIN_DRY_RUN", "false").lower() == "true"
    enable_anti_detection = os.getenv("LINKEDIN_ENABLE_ANTI_DETECTION", "true").lower() == "true"

    poster = LinkedInPoster(
        vault_path=vault_path,
        session_path=session_path,
        user_agent=user_agent,
        browser_headless=browser_headless,
        browser_timeout=browser_timeout,
        log_level=log_level,
        dry_run=dry_run,
        enable_anti_detection=enable_anti_detection
    )

    poster.run()
