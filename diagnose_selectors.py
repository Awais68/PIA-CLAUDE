#!/usr/bin/env python3
"""
Diagnostic script to find correct selectors for LinkedIn and WhatsApp
"""

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.automations.linkedin_playwright import LinkedInPlaywright
from src.automations.whatsapp_playwright import WhatsAppPlaywright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def diagnose_linkedin():
    """Find working LinkedIn selectors"""
    logger.info("\n" + "="*60)
    logger.info("🔵 DIAGNOSING LINKEDIN SELECTORS")
    logger.info("="*60 + "\n")

    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        logger.error("❌ Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD")
        return

    try:
        li = LinkedInPlaywright(email, password, headless=True)
        await li.login()

        if not li.page:
            logger.error("❌ Failed to get page object")
            return

        await li.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Test various selectors
        selectors_to_test = [
            # Original selectors
            "[data-test-id='start-post-button']",
            "[aria-label='Start a post']",
            "[aria-label='Post to your network']",
            "button[data-test-id='new-post-button']",
            ".share-creation-button",

            # Additional variations
            "button[aria-label*='post']",
            "button[aria-label*='Post']",
            "div[role='button'][aria-label*='post']",
            "[data-test-id*='post']",
            "[data-test-id*='start']",
            "button:has-text('Start')",

            # Generic selectors
            "button",
            "div[role='button']",
            "[contenteditable='true']",
        ]

        logger.info("🔍 Testing selectors...\n")

        found_selectors = []
        for selector in selectors_to_test:
            try:
                element = await li.page.query_selector(selector)
                if element:
                    # Get element text/content
                    text = await element.inner_text()
                    aria_label = await element.get_attribute("aria-label")
                    data_test = await element.get_attribute("data-testid")

                    info = f"  Selector: {selector}\n"
                    info += f"    Text: {text[:50]}\n" if text else ""
                    info += f"    Aria-label: {aria_label}\n" if aria_label else ""
                    info += f"    Data-testid: {data_test}\n" if data_test else ""

                    found_selectors.append((selector, text, aria_label))
                    logger.info("✅ " + info)
            except Exception as e:
                logger.debug(f"❌ {selector}: {e}")

        if found_selectors:
            logger.info("\n📋 FOUND SELECTORS (ranked by reliability):")
            for selector, text, label in found_selectors[:5]:
                logger.info(f"  • {selector}")
        else:
            logger.warning("\n⚠️  No selectors found")

        await li.close()

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def diagnose_whatsapp():
    """Find working WhatsApp selectors"""
    logger.info("\n" + "="*60)
    logger.info("🟢 DIAGNOSING WHATSAPP SELECTORS")
    logger.info("="*60 + "\n")

    try:
        wa = WhatsAppPlaywright(headless=False)
        await wa.login()

        if not wa.page:
            logger.error("❌ Failed to get page object")
            return

        await asyncio.sleep(2)

        # Test various selectors
        selectors_to_test = [
            # Original selectors
            "[data-testid='search-input']",
            "input[placeholder*='Search']",
            "input[placeholder*='search']",
            "input[aria-label*='Search']",

            # Variations
            "input[type='text']",
            "[contenteditable='true']",
            "[role='textbox']",
            "input",
            ".search",
            "#search",

            # For chat items
            "[data-testid='cell-frame-container']",
            "[role='option']",
            "[role='listitem']",
            "div[aria-label*='Chat']",
        ]

        logger.info("🔍 Testing selectors...\n")

        found_selectors = []
        for selector in selectors_to_test:
            try:
                elements = await wa.page.query_selector_all(selector)
                if elements:
                    logger.info(f"✅ {selector}: found {len(elements)} element(s)")
                    found_selectors.append(selector)
            except Exception as e:
                logger.debug(f"❌ {selector}: {e}")

        if found_selectors:
            logger.info("\n📋 FOUND SELECTORS:")
            for selector in found_selectors:
                logger.info(f"  • {selector}")
        else:
            logger.warning("\n⚠️  No selectors found")

        # Try to take a screenshot for manual inspection
        try:
            await wa.page.screenshot(path="whatsapp_debug.png")
            logger.info("\n📸 Screenshot saved: whatsapp_debug.png")
        except Exception as e:
            logger.warning(f"Could not save screenshot: {e}")

        await wa.close()

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    logger.info("\n🎭 SELECTOR DIAGNOSTIC TOOL")
    logger.info("=" * 60)

    await diagnose_linkedin()
    await diagnose_whatsapp()

    logger.info("\n" + "=" * 60)
    logger.info("✅ Diagnosis complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
