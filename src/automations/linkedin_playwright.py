"""
LinkedIn Automation using Playwright
Handles: Login, Post, Comment, Message, Like, Share
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Page, Browser
import logging

from src.playwright_utils import get_session_path, validate_session, screenshot_on_error

logger = logging.getLogger(__name__)

class LinkedInPlaywright:
    def __init__(self, email: str, password: str, headless: bool = True):
        self.email = email
        self.password = password
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.session_file = get_session_path("linkedin")

    async def login(self) -> bool:
        """Login to LinkedIn using Playwright"""
        try:
            self.playwright = await async_playwright().start()

            # Try loading saved session first
            if validate_session(self.session_file):
                logger.info("ℹ️ Loading saved LinkedIn session...")
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage'
                    ]
                )

                # Load stored session
                with open(self.session_file, 'r') as f:
                    state = json.load(f)

                context = await self.browser.new_context(storage_state=state)
                self.page = await context.new_page()

                # Anti-detection
                await self.page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => false});
                    window.chrome = {runtime: {}};
                """)

                # Test session is still valid
                await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                if "feed" in self.page.url:
                    logger.info("✅ LinkedIn session restored successfully")
                    return True
                else:
                    logger.warning("⚠️ Saved session expired, logging in fresh...")

            # Fresh login
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )
            self.page = await self.browser.new_page()

            # Anti-detection
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                window.chrome = {runtime: {}};
            """)

            logger.info("ℹ️ Navigating to LinkedIn login...")
            await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(1)

            logger.info(f"ℹ️ Entering credentials for {self.email}...")
            try:
                await self.page.fill("input#username", self.email, timeout=15000)
                await self.page.fill("input#password", self.password, timeout=15000)
            except Exception as e:
                logger.error(f"❌ Failed to fill credentials: {e}")
                await screenshot_on_error(self.page, "linkedin_login_failed")
                return False

            logger.info("ℹ️ Clicking submit...")
            try:
                await self.page.click("button[type='submit']")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"❌ Failed to submit login form: {e}")
                await screenshot_on_error(self.page, "linkedin_submit_failed")
                return False

            logger.info("ℹ️ Navigating to feed...")
            await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # Verify we're on feed
            if "feed" in self.page.url:
                logger.info("✅ LinkedIn login successful")

                # Save session
                try:
                    self.session_file.parent.mkdir(exist_ok=True)
                    state = await self.page.context.storage_state()
                    with open(self.session_file, 'w') as f:
                        json.dump(state, f)
                    logger.info(f"💾 Session saved to {self.session_file}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not save session: {e}")

                return True
            else:
                logger.error(f"❌ Not on feed page. URL: {self.page.url}")
                await screenshot_on_error(self.page, "linkedin_login_not_on_feed")
                return False

        except Exception as e:
            logger.error(f"❌ LinkedIn login failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def post_update(self, content: str, image_path: Optional[str] = None) -> bool:
        """Post an update to LinkedIn feed"""
        try:
            if not self.page:
                logger.error("❌ Page object is None")
                return False

            # Ensure we're on the feed
            logger.info("ℹ️ Navigating to feed page...")
            try:
                await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"❌ Failed to navigate to feed: {e}")
                return False

            # Use locator with text matching for "Start a post" (more reliable for React)
            logger.info("ℹ️ Looking for 'Start a post' element...")

            post_button = None
            try:
                # Try locator with text matching first (works with dynamic React content)
                post_button = self.page.locator("text='Start a post'").first
                await post_button.wait_for(timeout=5000)
                logger.info("✅ Found 'Start a post' via text locator")
            except Exception as e:
                logger.debug(f"Text locator failed: {e}")

                # Fallback to CSS selectors
                post_button_selectors = [
                    "[data-test-id='start-post-button']",
                    "[aria-label='Start a post']",
                    "[placeholder='Start a post']",
                    "input[placeholder='Start a post']",
                    ".share-creation-input",
                    "button[aria-label='Post to your network']",
                    ".share-creation-button"
                ]

                for selector in post_button_selectors:
                    try:
                        el = await self.page.query_selector(selector)
                        if el:
                            post_button = el
                            logger.info(f"✅ Found post input with selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector '{selector}' failed: {e}")
                        continue

            if not post_button:
                logger.error("❌ Could not find post input field")
                await screenshot_on_error(self.page, "linkedin_post_button_not_found")
                return False

            # Scroll into view and click
            try:
                if hasattr(post_button, 'scroll_into_view_if_needed'):
                    await post_button.scroll_into_view_if_needed()
                else:
                    await post_button.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await post_button.click()
                logger.info("ℹ️ Clicked post input, waiting for composer to load...")
                await asyncio.sleep(2.5)  # Wait for composer modal to appear
            except Exception as e:
                logger.error(f"❌ Failed to click post input: {e}")
                await screenshot_on_error(self.page, "linkedin_click_post_button_failed")
                return False

            # Try multiple selectors for the editor (ordered by stability)
            editor_selectors = [
                "[data-test-id='post-text-input']",
                "div.ql-editor[contenteditable='true']",
                "div[role='textbox'][contenteditable='true']",
                "div.share-creation-input",
                "[contenteditable='true']"
            ]

            editor = None
            for selector in editor_selectors:
                try:
                    editor = await self.page.query_selector(selector)
                    if editor:
                        logger.info(f"✅ Found editor with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Editor selector '{selector}' failed: {e}")
                    continue

            if not editor:
                logger.error("❌ Could not find post editor")
                await screenshot_on_error(self.page, "linkedin_editor_not_found")
                return False

            # Click editor to focus and add content
            try:
                await editor.scroll_into_view_if_needed()
                await editor.click()
                await asyncio.sleep(0.5)
                await editor.fill(content)
                logger.info(f"✅ Added content to post ({len(content)} characters)")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Failed to fill editor: {e}")
                await screenshot_on_error(self.page, "linkedin_fill_editor_failed")
                return False

            # Add image if provided
            if image_path and os.path.exists(image_path):
                try:
                    file_input = await self.page.query_selector("input[type='file']")
                    if file_input:
                        await file_input.set_input_files(image_path)
                        logger.info(f"✅ Added image: {os.path.basename(image_path)}")
                        await asyncio.sleep(1)
                except Exception as e:
                    logger.warning(f"⚠️ Could not add image: {e}")
            elif image_path:
                logger.warning(f"⚠️ Image path not found: {image_path}")

            # Post - try multiple selectors (ordered by stability)
            post_btn_selectors = [
                "[data-test-id='post-button']",
                "button.share-actions__primary-action",
                "div.share-box_actions button",
                "button[aria-label='Post']",
                "[aria-label='Publish post']",
                "button[data-test-id='share-button']"
            ]

            posted = False
            for selector in post_btn_selectors:
                try:
                    # Wait for button to be stable (1.6s for render completion)
                    btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if btn:
                        # Ensure button is visible and enabled
                        await btn.scroll_into_view_if_needed()
                        await asyncio.sleep(1.6)  # Wait for button to fully stabilize

                        is_disabled = await btn.get_attribute("disabled")
                        if is_disabled:
                            logger.debug(f"Button is disabled: {selector}")
                            continue

                        await btn.click()
                        posted = True
                        logger.info(f"✅ Clicked post button: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Post button selector '{selector}' failed: {e}")
                    continue

            if posted:
                await asyncio.sleep(3)
                logger.info(f"✅ Posted to LinkedIn: {content[:50]}...")
                return True
            else:
                logger.error("❌ Could not find or click post button")
                await screenshot_on_error(self.page, "linkedin_post_button_click_failed")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to post: {e}")
            import traceback
            traceback.print_exc()
            await screenshot_on_error(self.page, "linkedin_post_exception")
            return False

    async def read_feed(self, limit: int = 10) -> List[Dict]:
        """Read LinkedIn feed posts"""
        try:
            if not self.page:
                return []

            await self.page.goto("https://www.linkedin.com/feed/")
            await self.page.wait_for_load_state("networkidle")

            posts = []
            post_elements = await self.page.query_selector_all("article")

            for element in post_elements[:limit]:
                try:
                    author = await element.query_selector("a.app-aware-link[href*='/in/']")
                    content = await element.query_selector("span.break-words")
                    likes = await element.query_selector("span:has-text('like')")
                    comments = await element.query_selector("span:has-text('comment')")

                    post = {
                        "author": await author.text_content() if author else "Unknown",
                        "content": await content.text_content() if content else "",
                        "likes": await likes.text_content() if likes else "0",
                        "comments": await comments.text_content() if comments else "0",
                        "timestamp": datetime.now().isoformat()
                    }
                    posts.append(post)
                except Exception as e:
                    logger.debug(f"Could not parse post element: {e}")
                    continue

            logger.info(f"✅ Read {len(posts)} posts from LinkedIn feed")
            return posts
        except Exception as e:
            logger.error(f"❌ Failed to read feed: {e}")
            return []

    async def like_post(self, post_index: int = 0) -> bool:
        """Like a post by index"""
        try:
            if not self.page:
                return False

            like_buttons = await self.page.query_selector_all("button[aria-label*='like']")
            if post_index < len(like_buttons):
                await like_buttons[post_index].click()
                await asyncio.sleep(1)
                logger.info(f"✅ Liked post #{post_index}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to like post: {e}")
            return False

    async def send_message(self, recipient_name: str, message: str) -> bool:
        """Send a direct message"""
        try:
            if not self.page:
                return False

            # Open messaging
            await self.page.click("a[href='/messaging/']")
            await self.page.wait_for_load_state("networkidle")

            # Search for recipient
            await self.page.fill("input[placeholder='Search conversations']", recipient_name)
            await asyncio.sleep(1)

            # Select first result
            await self.page.click("a[role='option']")
            await self.page.wait_for_selector("div.msg-form__contenteditable")

            # Send message
            await self.page.fill("div.msg-form__contenteditable", message)
            await self.page.click("button[aria-label='Send']")
            await self.page.wait_for_load_state("networkidle")

            logger.info(f"✅ Sent message to {recipient_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False

    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            logger.info("LinkedIn browser closed")

    async def __aenter__(self):
        await self.login()
        return self

    async def __aexit__(self, *_args) -> None:  # noqa
        await self.close()


async def main():
    """Test LinkedIn automation"""
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        logger.error("❌ Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
        return

    async with LinkedInPlaywright(email, password, headless=False) as li:
        # Read feed
        posts = await li.read_feed(limit=3)
        for post in posts:
            print(f"📌 {post['author']}: {post['content'][:100]}")

        # Like first post
        await li.like_post(0)


if __name__ == "__main__":
    asyncio.run(main())
