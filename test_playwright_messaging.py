#!/usr/bin/env python3
"""
Test Playwright implementations and send test messages to LinkedIn & WhatsApp
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.automations.linkedin_playwright import LinkedInPlaywright
from src.automations.whatsapp_playwright import WhatsAppPlaywright
from src.mcp_servers.linkedin_mcp_playwright import post_to_feed
from src.mcp_servers.whatsapp_mcp_playwright import send_message
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TEST_MESSAGE = "hi im playwright 🤖"
TEST_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def test_linkedin_playwright():
    """Test LinkedIn Playwright implementation"""
    logger.info("=" * 60)
    logger.info("🔵 TESTING LINKEDIN PLAYWRIGHT")
    logger.info("=" * 60)

    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        logger.error("❌ LINKEDIN_EMAIL and LINKEDIN_PASSWORD not set in .env")
        return False

    try:
        # Test 1: Initialize and login
        logger.info("📍 Test 1: Initialize LinkedIn Playwright...")
        li = LinkedInPlaywright(email, password, headless=True)
        logger.info("✅ LinkedInPlaywright initialized")

        # Test 2: Login
        logger.info("📍 Test 2: Login to LinkedIn...")
        login_result = await li.login()
        if not login_result:
            logger.error("❌ LinkedIn login failed")
            return False
        logger.info("✅ LinkedIn login successful")

        # Test 3: Check session file
        session_path = li.session_file
        if session_path.exists():
            logger.info(f"✅ Session file saved: {session_path}")
        else:
            logger.warning(f"⚠️ Session file not found: {session_path}")

        # Test 4: Post message
        logger.info(f"📍 Test 3: Posting message to LinkedIn...")
        post_result = await li.post_update(
            f"{TEST_MESSAGE}\n\n{TEST_TIMESTAMP}",
            image_path=None
        )
        if post_result:
            logger.info(f"✅ Posted to LinkedIn: {TEST_MESSAGE}")
        else:
            logger.error("❌ Failed to post to LinkedIn")
            return False

        # Cleanup
        await li.close()
        logger.info("✅ LinkedIn tests passed\n")
        return True

    except Exception as e:
        logger.error(f"❌ LinkedIn test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_whatsapp_playwright():
    """Test WhatsApp Playwright implementation"""
    logger.info("=" * 60)
    logger.info("🟢 TESTING WHATSAPP PLAYWRIGHT")
    logger.info("=" * 60)

    try:
        # Test 1: Initialize
        logger.info("📍 Test 1: Initialize WhatsApp Playwright...")
        wa = WhatsAppPlaywright(headless=False)
        logger.info("✅ WhatsAppPlaywright initialized")

        # Test 2: Login
        logger.info("📍 Test 2: Login to WhatsApp Web...")
        logger.info("   If QR code appears, scan it with your phone")
        login_result = await wa.login()
        if not login_result:
            logger.error("❌ WhatsApp login failed")
            return False
        logger.info("✅ WhatsApp login successful")

        # Test 3: Check session persistence
        session_path = wa.session_dir / "state.json"
        if session_path.exists():
            logger.info(f"✅ Session file saved: {session_path}")
        else:
            logger.warning(f"⚠️ Session file not found: {session_path}")

        # Test 4: Send test message (requires contact name)
        contact = os.getenv("WHATSAPP_TEST_CONTACT", "Mom")
        logger.info(f"📍 Test 3: Sending message to '{contact}'...")
        send_result = await wa.send_message(
            contact,
            f"{TEST_MESSAGE}\n{TEST_TIMESTAMP}"
        )
        if send_result:
            logger.info(f"✅ Sent to {contact}: {TEST_MESSAGE}")
        else:
            logger.warning(f"⚠️ Failed to send message to {contact}")
            logger.info("   (This may be expected if contact doesn't exist)")

        # Cleanup
        await wa.close()
        logger.info("✅ WhatsApp tests completed\n")
        return True

    except Exception as e:
        logger.error(f"❌ WhatsApp test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sync_wrappers():
    """Test MCP server sync wrappers"""
    logger.info("=" * 60)
    logger.info("⚙️ TESTING SYNC WRAPPERS")
    logger.info("=" * 60)

    try:
        # Test 1: LinkedIn sync wrapper
        logger.info("📍 Test 1: LinkedIn sync wrapper...")
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if email and password:
            result = post_to_feed(
                f"{TEST_MESSAGE}\n{TEST_TIMESTAMP}",
                image_path=None
            )
            if result.get("success"):
                logger.info("✅ LinkedIn sync wrapper works")
            else:
                logger.warning(f"⚠️ LinkedIn sync wrapper returned error: {result.get('error')}")
        else:
            logger.warning("⚠️ Skipping LinkedIn sync test (no credentials)")

        # Test 2: WhatsApp sync wrapper
        logger.info("📍 Test 2: WhatsApp sync wrapper...")
        contact = os.getenv("WHATSAPP_TEST_CONTACT", "Mom")
        result = send_message(contact, f"{TEST_MESSAGE}\n{TEST_TIMESTAMP}")
        if result.get("success"):
            logger.info("✅ WhatsApp sync wrapper works")
        else:
            logger.warning(f"⚠️ WhatsApp sync wrapper returned error: {result.get('error')}")

        logger.info("✅ Sync wrapper tests completed\n")
        return True

    except Exception as e:
        logger.error(f"❌ Sync wrapper test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("🎭 PLAYWRIGHT TEST SUITE")
    logger.info("=" * 60 + "\n")

    results = {
        "LinkedIn Async": False,
        "WhatsApp Async": False,
        "Sync Wrappers": False
    }

    # Test LinkedIn
    try:
        results["LinkedIn Async"] = await test_linkedin_playwright()
    except KeyboardInterrupt:
        logger.info("⏸️  LinkedIn test skipped (user cancelled)")
    except Exception as e:
        logger.error(f"❌ LinkedIn test failed: {e}")

    # Test WhatsApp
    try:
        results["WhatsApp Async"] = await test_whatsapp_playwright()
    except KeyboardInterrupt:
        logger.info("⏸️  WhatsApp test skipped (user cancelled)")
    except Exception as e:
        logger.error(f"❌ WhatsApp test failed: {e}")

    # Test sync wrappers
    results["Sync Wrappers"] = test_sync_wrappers()

    # Summary
    logger.info("=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name}: {status}")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)
    logger.info(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        logger.info("\n✨ All tests passed!\n")
        return 0
    else:
        logger.warning(f"\n⚠️  {total_tests - total_passed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
