"""
WhatsApp Automation using Playwright
Handles: Send Message, Read Messages, Forward, React, Status
Uses persistent storage state for permanent session persistence (one-time QR scan only)
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import logging

from src.playwright_utils import get_session_path, validate_session, screenshot_on_error

logger = logging.getLogger(__name__)

# Session state file for permanent persistence
STATE_FILE = Path(os.getcwd()) / "whatsapp_session.json"

class WhatsAppPlaywright:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.session_dir = get_session_path("whatsapp").parent

    async def login(self) -> bool:
        """Login to WhatsApp Web with permanent session persistence (one-time QR scan)"""
        try:
            self.playwright = await async_playwright().start()

            logger.info("ℹ️ Launching browser...")
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage'
                ]
            )

            # Try to load saved session state first (one-time QR scan only)
            storage_state = None
            session_exists = STATE_FILE.exists()

            if session_exists:
                try:
                    with open(STATE_FILE, 'r') as f:
                        storage_state = json.load(f)
                    logger.info("✅ Loaded saved session - no QR needed!")
                except Exception as e:
                    logger.warning(f"⚠️ Could not load session: {e}")
                    session_exists = False

            # Create context with saved state if available
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                storage_state=storage_state
            )
            self.page = await self.context.new_page()

            if not session_exists:
                logger.info("🆕 New session - QR code scan required (one time only)")

            logger.info("ℹ️ Navigating to WhatsApp Web...")
            try:
                await self.page.goto("https://web.whatsapp.com/", wait_until="networkidle")
            except Exception as e:
                logger.warning(f"⚠️ Navigation timeout (network may be slow): {e}")
                # Continue anyway, may still load

            # Wait for page to stabilize
            await asyncio.sleep(2)

            # Check if we're already logged in or need to scan QR
            qr_element = None
            try:
                qr_element = await self.page.query_selector("canvas")
                if qr_element:
                    logger.info("🔐 QR code detected - Please scan with your phone")
                    # Wait for successful login (QR disappears)
                    for attempt in range(120):  # 120 seconds max
                        if not await self.page.query_selector("canvas"):
                            logger.info("✅ QR code scanned successfully")
                            break
                        if attempt % 10 == 0:
                            logger.info(f"   Waiting for QR scan... ({attempt}s)")
                        await asyncio.sleep(1)
                else:
                    logger.info("ℹ️ Using existing WhatsApp Web session")
            except Exception as e:
                logger.debug(f"Could not check for QR code: {e}")

            # Wait for chat list or main interface to load
            # Use ONLY data-testid selectors (stable across WhatsApp updates)
            chat_loaded = False
            selectors = [
                "[data-testid='chat-list']",
                "[role='listitem']",
                "div[aria-label*='Chat']"
            ]

            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=10000)
                    logger.info(f"✅ Chat interface loaded (selector: {selector})")
                    chat_loaded = True
                    break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' timeout: {e}")
                    continue

            if not chat_loaded:
                logger.warning("⚠️ Could not detect chat list, but continuing...")

            # Wait a bit more for UI to fully render
            await asyncio.sleep(2)

            # Save session state
            await self._save_session()

            logger.info("✅ WhatsApp login successful")
            return True

        except Exception as e:
            logger.error(f"❌ WhatsApp login failed: {e}")
            import traceback
            traceback.print_exc()
            if self.page:
                await screenshot_on_error(self.page, "whatsapp_login_failed")
            return False

    async def send_message(self, contact_name: str, message: str) -> bool:
        """Send a message to a contact"""
        try:
            if not self.page:
                logger.error("❌ Page is not initialized")
                return False

            logger.info(f"ℹ️ Sending message to {contact_name}...")
            await asyncio.sleep(1)

            # Step 1: Find search input using stable selectors
            logger.info("ℹ️ Looking for search input...")
            search_input = None
            search_selectors = [
                "[data-testid='search-input']",
                "div[contenteditable='true'][aria-placeholder*='Search']",
                "div[contenteditable='true'][role='textbox']",
                "div.lexical-rich-text-input",
                "input[placeholder*='Search']",
                "input[placeholder*='search']",
                "input[aria-label*='Search']"
            ]

            for selector in search_selectors:
                try:
                    elem = await self.page.query_selector(selector)
                    if elem:
                        logger.info(f"✅ Found search input: {selector}")
                        search_input = elem
                        break
                except Exception as e:
                    logger.debug(f"Search selector '{selector}' failed: {e}")
                    continue

            if not search_input:
                logger.error("❌ Could not find search input")
                await screenshot_on_error(self.page, "whatsapp_search_input_not_found")
                return False

            # Step 2: Search for contact
            try:
                await search_input.click()
                await asyncio.sleep(0.5)
                await search_input.fill(contact_name)
                logger.info(f"ℹ️ Searching for '{contact_name}'...")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"❌ Failed to search for contact: {e}")
                await screenshot_on_error(self.page, "whatsapp_search_failed")
                return False

            # Step 3: Find and click the chat row for this contact
            logger.info(f"ℹ️ Looking for chat with '{contact_name}'...")

            # Better chat row selectors (2025-2026 WhatsApp Web structure)
            chat_selectors = [
                "div[role='listitem']",                      # basic chat row
                f"span[title='{contact_name}']",             # exact name match
                "div._ak8o._ak8p._ak8q._ak8r",              # class-based selector
                f"div[title*='{contact_name}']",            # title attribute match
                "div[aria-label*='Open chat']"              # aria fallback
            ]

            contact_clicked = False
            for selector in chat_selectors:
                try:
                    chat_elem = self.page.locator(selector).first
                    is_visible = await chat_elem.is_visible(timeout=2000)
                    if is_visible:
                        logger.info(f"✅ Found chat with selector: {selector}")
                        await chat_elem.click()
                        contact_clicked = True
                        logger.info(f"✅ Clicked chat for '{contact_name}'")
                        await asyncio.sleep(2)
                        break
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")
                    continue

            if not contact_clicked:
                logger.warning("⚠️ Could not find/click contact chat")
                await screenshot_on_error(self.page, "whatsapp_contact_not_found")
                return False

            # Step 3b: Wait for chat window and message input to fully load
            try:
                # Wait for message input with data-tab='10'
                await self.page.wait_for_selector(
                    "div[contenteditable='true'][data-tab='10']",
                    timeout=5000
                )
                logger.info("✅ Chat window opened successfully")
                await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Chat loading may be slow: {e}")
                await asyncio.sleep(2)

            # Step 4: Find message input using data-tab='10' (main message box)
            logger.info("ℹ️ Looking for message input...")
            msg_input = None

            # Primary selector: data-tab='10' for message input
            msg_selectors = [
                "div[contenteditable='true'][data-tab='10']",     # main message box
                "div[title='Type a message']",
                "div[role='textbox'][contenteditable='true']",
                "[data-testid='conversation-compose-box-input']"
            ]

            for selector in msg_selectors:
                try:
                    elem = await self.page.query_selector(selector)
                    if elem:
                        logger.info(f"✅ Found message input: {selector}")
                        msg_input = elem
                        break
                except Exception as e:
                    logger.debug(f"Message selector '{selector}' failed: {e}")
                    continue

            if not msg_input:
                logger.error("❌ Could not find message input")
                await screenshot_on_error(self.page, "whatsapp_message_input_not_found")
                return False

            # Step 5: Type message and send
            try:
                await msg_input.click()
                await asyncio.sleep(0.5)

                # Type message character by character for reliability
                await msg_input.type(message, delay=5)
                logger.info(f"✅ Typed message ({len(message)} characters)")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Failed to type message: {e}")
                await screenshot_on_error(self.page, "whatsapp_fill_message_failed")
                return False

            # Step 6: Send message via Enter key
            try:
                logger.info("ℹ️ Sending message...")
                await msg_input.press("Enter")
                logger.info("✅ Message sent!")
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"❌ Failed to send message: {e}")
                # Try finding and clicking send button as fallback
                try:
                    send_btn = await self.page.query_selector("button[aria-label='Send']")
                    if send_btn:
                        await send_btn.click()
                        await asyncio.sleep(2)
                        logger.info("✅ Message sent via button!")
                    else:
                        raise Exception("No send button found")
                except Exception as e2:
                    logger.error(f"❌ Send button also failed: {e2}")
                    await screenshot_on_error(self.page, "whatsapp_send_failed")
                    return False

            logger.info(f"✅ Successfully sent message to {contact_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            import traceback
            traceback.print_exc()
            await screenshot_on_error(self.page, "whatsapp_send_exception")
            return False

    async def read_messages(self, contact_name: str, limit: int = 10) -> List[Dict]:
        """Read messages from a contact"""
        try:
            if not self.page:
                return []

            # Search for contact
            search_box = None
            try:
                search_box = await self.page.query_selector("div[contenteditable='true'][role='textbox']")
            except:
                search_box = await self.page.query_selector("[data-testid='search-input']")
            if search_box:
                try:
                    await search_box.fill(contact_name)
                    await asyncio.sleep(1)

                    chat_item = await self.page.query_selector("[role='listitem']")
                    if chat_item:
                        await chat_item.click()
                        await asyncio.sleep(1)
                except Exception as e:
                    logger.warning(f"⚠️ Could not search for contact: {e}")

            # Read messages
            messages = []
            try:
                msg_elements = await self.page.query_selector_all("[data-testid='msg-container']")
            except Exception as e:
                logger.warning(f"⚠️ Could not find message containers: {e}")
                return messages

            for element in msg_elements[-limit:]:
                try:
                    sender = await element.query_selector("[class*='message-in'], [class*='message-out']")
                    text = await element.query_selector("[class*='selectable-text']")
                    time = await element.query_selector("[data-testid='message_timestamp']")

                    msg = {
                        "sender": "Me" if sender and "message-out" in (await sender.get_attribute("class") or "") else contact_name,
                        "text": await text.text_content() if text else "",
                        "time": await time.text_content() if time else "",
                        "timestamp": datetime.now().isoformat()
                    }
                    messages.append(msg)
                except Exception as e:
                    logger.debug(f"Could not parse message element: {e}")
                    continue

            logger.info(f"✅ Read {len(messages)} messages from {contact_name}")
            return messages
        except Exception as e:
            logger.error(f"❌ Failed to read messages: {e}")
            return []

    async def send_media(self, contact_name: str, media_path: str, caption: str = "") -> bool:
        """Send an image or video with caption"""
        try:
            if not self.page or not os.path.exists(media_path):
                return False

            # Search for contact
            search_box = await self.page.query_selector("div[contenteditable='true'][role='textbox']")
            if not search_box:
                search_box = await self.page.query_selector("input[placeholder='Search or start new chat']")

            if search_box:
                await search_box.fill(contact_name)
                await asyncio.sleep(1)

                chat_item = await self.page.query_selector("[role='listitem']")
                if chat_item:
                    await chat_item.click()
                    await asyncio.sleep(1)

            # Click attachment button
            attach_btn = await self.page.query_selector("button[aria-label='Attach']")
            if attach_btn:
                await attach_btn.click()
                await asyncio.sleep(0.5)

            # Upload file
            file_input = await self.page.query_selector("input[type='file']")
            if file_input:
                await file_input.set_input_files(media_path)
                await asyncio.sleep(2)

            # Add caption if provided
            if caption:
                caption_input = await self.page.query_selector("[contenteditable='true']")
                if caption_input:
                    await caption_input.fill(caption)

            # Send
            send_btn = await self.page.query_selector("button[aria-label='Send']")
            if send_btn:
                await send_btn.click()
                await asyncio.sleep(1)

            logger.info(f"✅ Sent media to {contact_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send media: {e}")
            return False

    async def react_to_message(self, emoji: str) -> bool:
        """React to the last message with an emoji"""
        try:
            if not self.page:
                return False

            # Right-click on last message
            last_msg = await self.page.query_selector("[data-testid='msg-container']:last-of-type")
            if last_msg:
                await last_msg.click(button="right")
                await asyncio.sleep(0.5)

                # Click react option
                react_btn = await self.page.query_selector("button:has-text('React')")
                if react_btn:
                    await react_btn.click()
                    await asyncio.sleep(0.5)

                    # Select emoji
                    emoji_elem = await self.page.query_selector(f"span:text('{emoji}')")
                    if emoji_elem:
                        await emoji_elem.click()
                        await asyncio.sleep(0.5)

                    logger.info(f"✅ Reacted with {emoji}")
                    return True

            return False
        except Exception as e:
            logger.error(f"❌ Failed to react: {e}")
            return False

    async def get_status(self, contact_name: str) -> Optional[str]:
        """Get last seen/status of a contact"""
        try:
            if not self.page:
                return None

            # Search for contact
            search_box = await self.page.query_selector("div[contenteditable='true'][role='textbox']")
            if not search_box:
                search_box = await self.page.query_selector("input[placeholder='Search or start new chat']")

            if search_box:
                await search_box.fill(contact_name)
                await asyncio.sleep(1)

                chat_item = await self.page.query_selector("[role='listitem']")
                if chat_item:
                    await chat_item.click()
                    await asyncio.sleep(1)

                    # Get status/last seen
                    status = await self.page.query_selector("span[title*='last seen']")
                    if not status:
                        status = await self.page.query_selector("span:text('online')")

                    if status:
                        result = await status.text_content()
                        logger.info(f"ℹ️ {contact_name} - {result}")
                        return result

            return None
        except Exception as e:
            logger.error(f"❌ Failed to get status: {e}")
            return None

    async def _save_session(self):
        """Save current session state for permanent reuse (one-time QR scan persistence)"""
        try:
            state = await self.context.storage_state()
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f)
            logger.info(f"💾 Session saved permanently: {STATE_FILE}")
            logger.info("✅ Next run will use saved session (no QR needed)")
        except Exception as e:
            logger.warning(f"⚠️ Could not save session: {e}")

    async def close(self):
        """Close browser and context"""
        try:
            # Save session state before closing
            if self.context:
                await self._save_session()

            if self.context:
                await self.context.close()
                logger.info("WhatsApp context closed")
            if self.browser:
                await self.browser.close()
                logger.info("WhatsApp browser closed")
            if self.playwright:
                await self.playwright.stop()
                logger.info("Playwright stopped")
        except Exception as e:
            logger.warning(f"⚠️ Error during cleanup: {e}")

    async def __aenter__(self):
        await self.login()
        return self

    async def __aexit__(self, *_args) -> None:  # noqa
        await self.close()


async def main():
    """Test WhatsApp automation"""
    async with WhatsAppPlaywright(headless=False) as wa:
        # Send message
        await wa.send_message("Mom", "Hi Mom! This is from automation 🤖")

        # Read messages
        messages = await wa.read_messages("Mom", limit=5)
        for msg in messages:
            print(f"💬 {msg['sender']}: {msg['text']}")


if __name__ == "__main__":
    asyncio.run(main())
