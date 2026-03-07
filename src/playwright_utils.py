"""
Shared Playwright Utilities
Centralized session management, error handling, and element finding
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def get_session_path(service: str) -> Path:
    """
    Get canonical session path for a service

    Args:
        service: 'linkedin' or 'whatsapp'

    Returns:
        Path to session file
    """
    session_dir = Path.cwd() / f"{service}_session"
    return session_dir / "state.json"


def validate_session(path: Path) -> bool:
    """
    Validate that a saved session file is valid

    Args:
        path: Path to session JSON file

    Returns:
        True if session exists, is valid JSON, and has cookies
    """
    if not path.exists():
        return False

    try:
        with open(path, 'r') as f:
            state = json.load(f)

        # Check if cookies exist and not empty
        if not state.get('cookies'):
            logger.warning(f"⚠️ Session at {path} has no cookies")
            return False

        logger.info(f"✅ Valid session found at {path}")
        return True

    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"⚠️ Invalid session file: {e}")
        return False


def safe_async_run(coro):
    """
    Safely run async code from sync context
    Handles "event loop already running" error

    Args:
        coro: Async coroutine to run

    Returns:
        Result of coroutine
    """
    try:
        # Check if event loop already running
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, create one
        return asyncio.run(coro)

    # Event loop already running (nested context)
    # Use nest_asyncio or run in thread pool
    try:
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(coro)
    except ImportError:
        # Fallback: run in thread pool
        import concurrent.futures
        import threading

        result = None
        exception = None

        def run_in_thread():
            nonlocal result, exception
            try:
                result = asyncio.run(coro)
            except Exception as e:
                exception = e

        thread = threading.Thread(target=run_in_thread, daemon=False)
        thread.start()
        thread.join()

        if exception:
            raise exception
        return result


async def find_element(page, selectors: List[str], timeout: int = 5000):
    """
    Try multiple selectors in order, return first match
    Logs which selector successfully matched

    Args:
        page: Playwright page object
        selectors: List of CSS selectors to try
        timeout: Timeout in milliseconds

    Returns:
        First matching element, or None
    """
    for selector in selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                logger.info(f"✅ Found element with selector: {selector}")
                return element
        except Exception as e:
            logger.debug(f"⚠️ Selector '{selector}' failed: {e}")
            continue

    logger.warning(f"❌ None of {len(selectors)} selectors matched")
    return None


async def screenshot_on_error(page, context: str) -> Optional[str]:
    """
    Take screenshot and save for debugging

    Args:
        page: Playwright page object
        context: Label for the screenshot (e.g., "linkedin_login_failed")

    Returns:
        Path to screenshot if successful
    """
    try:
        error_dir = Path.cwd() / "playwright_errors"
        error_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{context}_{timestamp}.png"
        filepath = error_dir / filename

        await page.screenshot(path=str(filepath))
        logger.info(f"📸 Error screenshot saved: {filepath}")
        return str(filepath)

    except Exception as e:
        logger.warning(f"⚠️ Could not save screenshot: {e}")
        return None


async def wait_for_selector_safe(page, selectors: List[str], timeout: int = 10000):
    """
    Wait for any of the selectors to appear

    Args:
        page: Playwright page object
        selectors: List of selectors to wait for
        timeout: Timeout in milliseconds

    Returns:
        The selector that appeared, or None
    """
    start_time = asyncio.get_event_loop().time()

    while True:
        elapsed = (asyncio.get_event_loop().time() - start_time) * 1000
        if elapsed > timeout:
            logger.warning(f"❌ Timeout waiting for selectors: {selectors}")
            return None

        for selector in selectors:
            try:
                if await page.query_selector(selector):
                    logger.info(f"✅ Selector appeared: {selector}")
                    return selector
            except Exception:
                pass

        await asyncio.sleep(0.5)
