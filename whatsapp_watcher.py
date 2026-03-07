"""
WhatsApp Watcher using Playwright

Monitors WhatsApp Web for messages containing keywords and creates action files.
Uses persistent browser context to save login session across restarts.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from playwright.sync_api import sync_playwright, BrowserContext, Page
from base_watcher import BaseWatcher


@dataclass
class WhatsAppMessage:
    """Represents a WhatsApp message to process."""
    sender_name: str
    message_text: str
    timestamp: str
    keywords_matched: List[str]
    message_id: str  # Unique identifier to prevent duplicates


class WhatsAppWatcher(BaseWatcher):
    """
    Monitor WhatsApp Web for messages with specific keywords.

    Features:
    - Persistent browser session (login saved)
    - Keyword-based filtering
    - Duplicate detection using processed_ids.json
    - Headless or visible browser mode
    - Configurable timeouts and retry logic
    """

    WHATSAPP_URL = "https://web.whatsapp.com"
    MAX_RETRIES = 3
    RETRY_WAIT = 2  # seconds

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        keywords: List[str],
        check_interval: int = 30,
        browser_headless: bool = True,
        browser_timeout: int = 60,
        log_level: str = "INFO",
        dry_run: bool = False
    ):
        """
        Initialize WhatsApp Watcher.

        Args:
            vault_path: Path to Obsidian vault
            session_path: Path to save browser session
            keywords: List of keywords to watch for
            check_interval: Seconds between checks (default: 30)
            browser_headless: Run browser in headless mode (default: True)
            browser_timeout: Timeout in seconds for page loads (default: 60)
            log_level: Logging level (default: INFO)
            dry_run: If True, log actions but don't create files (default: False)
        """
        super().__init__(vault_path, check_interval, log_level)

        self.session_path = Path(session_path).resolve()
        self.keywords = [kw.lower().strip() for kw in keywords]
        self.browser_headless = browser_headless
        self.browser_timeout = browser_timeout
        self.dry_run = dry_run

        # Setup processed message IDs tracking
        self.processed_ids_file = Path("processed_ids.json")
        self.processed_ids = self._load_processed_ids()

        # Browser instance (will be created on first use)
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

        self.logger.info(f"WhatsApp Watcher initialized")
        self.logger.info(f"  Keywords: {', '.join(self.keywords)}")
        self.logger.info(f"  Session path: {self.session_path}")
        self.logger.info(f"  Headless: {self.browser_headless}")
        self.logger.info(f"  Dry run: {self.dry_run}")

    def _load_processed_ids(self) -> set:
        """
        Load previously processed message IDs from file.

        Returns:
            Set of message IDs that have been processed
        """
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

    def _init_browser(self) -> None:
        """
        Initialize Playwright browser with persistent context.

        Creates a persistent context so session is saved between runs.
        """
        if self.browser is not None:
            return  # Already initialized

        try:
            self.logger.debug("Initializing Playwright browser...")
            self.playwright = sync_playwright().start()

            # Create session directory if it doesn't exist
            self.session_path.mkdir(parents=True, exist_ok=True)

            # Launch browser with persistent context
            self.browser = self.playwright.chromium.launch(
                headless=self.browser_headless
            )

            self.context = self.browser.new_context(
                storage_state=str(self.session_path / "state.json")
                if (self.session_path / "state.json").exists()
                else None
            )

            self.page = self.context.new_page()
            self.page.set_default_timeout(self.browser_timeout * 1000)

            self.logger.info("Browser initialized")

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

    def check_for_updates(self) -> List[WhatsAppMessage]:
        """
        Check WhatsApp Web for unread messages with keywords.

        Process:
        1. Initialize/reuse browser
        2. Navigate to WhatsApp Web
        3. Wait for chat list to load
        4. Find unread chats
        5. Extract messages and filter by keywords
        6. Return list of messages

        Returns:
            List of WhatsAppMessage objects with matching keywords
        """
        messages = []

        try:
            # Initialize browser if needed
            if self.browser is None:
                self._init_browser()

            # Navigate to WhatsApp
            self.logger.debug(f"Navigating to {self.WHATSAPP_URL}")
            self.page.goto(self.WHATSAPP_URL, wait_until="networkidle", timeout=30000)

            # Wait for chat list to load
            try:
                self.page.wait_for_selector('[data-testid="pane-side"]', timeout=self.browser_timeout * 1000)
                self.logger.debug("Chat list loaded")
            except Exception as e:
                self.logger.warning(f"Chat list did not load: {e}")
                # If chat list doesn't load, assume not logged in
                return messages

            # Find all chat items
            chat_items = self.page.query_selector_all('[data-testid="chat"]')
            self.logger.debug(f"Found {len(chat_items)} chat items")

            for chat_item in chat_items:
                try:
                    # Check if chat has unread indicator
                    unread_span = chat_item.query_selector('[data-testid="unread-badge"]')
                    if not unread_span:
                        continue  # Skip read chats

                    # Get sender name
                    name_elem = chat_item.query_selector('[title]')
                    if not name_elem:
                        continue

                    sender_name = name_elem.get_attribute('title')
                    if not sender_name:
                        continue

                    self.logger.debug(f"Processing unread chat from: {sender_name}")

                    # Click chat to open it
                    chat_item.click()
                    self.page.wait_for_timeout(500)  # Brief wait for chat to open

                    # Get last few messages
                    message_elements = self.page.query_selector_all('[data-testid="msg-container"]')

                    for msg_elem in message_elements[-5:]:  # Check last 5 messages
                        try:
                            # Get message text
                            text_elem = msg_elem.query_selector('[data-testid="msg-text"]')
                            if not text_elem:
                                continue

                            message_text = text_elem.inner_text()
                            if not message_text:
                                continue

                            # Get timestamp
                            time_elem = msg_elem.query_selector('[data-testid="msg-time"]')
                            timestamp = time_elem.get_attribute('data-time') if time_elem else datetime.now().isoformat()

                            # Create unique message ID
                            message_id = f"{sender_name}_{timestamp}_{hash(message_text) & 0x7fffffff}"

                            # Skip if already processed
                            if message_id in self.processed_ids:
                                continue

                            # Check for keywords
                            message_lower = message_text.lower()
                            matched_keywords = [
                                kw for kw in self.keywords
                                if kw in message_lower
                            ]

                            if matched_keywords:
                                msg = WhatsAppMessage(
                                    sender_name=sender_name,
                                    message_text=message_text,
                                    timestamp=timestamp,
                                    keywords_matched=matched_keywords,
                                    message_id=message_id
                                )
                                messages.append(msg)
                                self.processed_ids.add(message_id)
                                self.logger.info(
                                    f"Found message from {sender_name}: {matched_keywords}"
                                )

                        except Exception as e:
                            self.logger.debug(f"Error processing message: {e}")
                            continue

                except Exception as e:
                    self.logger.debug(f"Error processing chat: {e}")
                    continue

            # Save processed IDs
            if messages:
                self._save_processed_ids()

        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}", exc_info=True)

        return messages

    def create_action_file(self, message: WhatsAppMessage) -> None:
        """
        Create markdown action file from a WhatsApp message.

        File format:
        - YAML frontmatter with metadata
        - Message content section
        - Keywords detected section
        - Suggested actions checklist
        - Draft reply section

        Args:
            message: WhatsAppMessage object to create file from
        """
        try:
            # Parse timestamp
            try:
                msg_time = datetime.fromisoformat(message.timestamp)
            except:
                msg_time = datetime.now()

            # Create filename
            filename = (
                f"WHATSAPP_{msg_time.strftime('%Y%m%d_%H%M%S')}_"
                f"{message.sender_name.replace(' ', '_')}.md"
            )

            filepath = self.needs_action_path / filename

            # Determine priority based on keywords
            priority = "high" if any(kw in ["urgent", "asap", "emergency"] for kw in message.keywords_matched) else "normal"

            # Create markdown content
            content = f"""---
type: whatsapp_message
from: {message.sender_name}
received: {message.timestamp}
priority: {priority}
status: pending
keywords_matched:
{chr(10).join(f'  - {kw}' for kw in message.keywords_matched)}
---

## WhatsApp Message

**From:** {message.sender_name}
**Received:** {msg_time.strftime('%Y-%m-%d %H:%M %p')}

### Message Content
"{message.message_text}"

### Keywords Detected
{chr(10).join(f'- {kw} ✓' for kw in message.keywords_matched)}

## Suggested Actions
- [ ] Reply to sender
- [ ] Gather required information
- [ ] Take appropriate action
- [ ] Mark as done when complete

## Draft Reply
*(Claude will fill this section when processing)*

---
*Created by WhatsApp Watcher v1.0 at {datetime.now().isoformat()}*
"""

            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would create: {filepath}")
                self.logger.info(f"[DRY RUN] Content preview:\n{content[:200]}...")
            else:
                # Write file
                filepath.write_text(content, encoding='utf-8')
                self.logger.info(f"Created action file: {filepath}")

        except Exception as e:
            self.logger.error(f"Error creating action file: {e}", exc_info=True)

    def stop(self) -> None:
        """Stop the watcher and cleanup resources."""
        super().stop()
        self._cleanup_browser()


if __name__ == "__main__":
    # Example usage (for testing)
    from dotenv import load_dotenv
    import os

    load_dotenv()

    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./AI_Employee_Vault")
    session_path = os.getenv("WHATSAPP_WATCHER_SESSION_PATH", "./whatsapp_session")
    keywords_str = os.getenv("WHATSAPP_WATCHER_KEYWORDS", "urgent,asap,invoice,payment")
    keywords = [k.strip() for k in keywords_str.split(",")]
    check_interval = int(os.getenv("WHATSAPP_WATCHER_CHECK_INTERVAL", "30"))
    browser_headless = os.getenv("WHATSAPP_WATCHER_BROWSER_HEADLESS", "true").lower() == "true"
    browser_timeout = int(os.getenv("WHATSAPP_WATCHER_BROWSER_TIMEOUT", "60"))
    log_level = os.getenv("WHATSAPP_WATCHER_LOG_LEVEL", "INFO")
    dry_run = os.getenv("WHATSAPP_WATCHER_DRY_RUN", "false").lower() == "true"

    watcher = WhatsAppWatcher(
        vault_path=vault_path,
        session_path=session_path,
        keywords=keywords,
        check_interval=check_interval,
        browser_headless=browser_headless,
        browser_timeout=browser_timeout,
        log_level=log_level,
        dry_run=dry_run
    )

    watcher.run()
