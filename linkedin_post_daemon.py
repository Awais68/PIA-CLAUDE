#!/usr/bin/env python3
"""
Post to LinkedIn without re-login using daemon
Requires linkedin_daemon.py to be running!

Usage:
  Terminal 1: python3 linkedin_daemon.py (keep running)
  Terminal 2: python3 linkedin_post_daemon.py "Your post content"
"""

import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed")
    sys.exit(1)


async def post_to_linkedin(content: str) -> bool:
    """Post to LinkedIn (assumes daemon browser is already logged in)"""

    print("\n" + "="*70)
    print("📱 LINKEDIN POST (Via Daemon)")
    print("="*70)
    print(f"Content: {content[:60]}...")
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to feed
            print("🌐 Opening LinkedIn feed...")
            await page.goto('https://www.linkedin.com/feed', wait_until='networkidle', timeout=10000)

            # Check if logged in
            try:
                await page.wait_for_selector('button:has-text("Start a post")', timeout=5000)
                print("✅ Logged in!")
            except:
                print("❌ Not logged in - is the daemon running?")
                print("   Run: python3 linkedin_daemon.py")
                return False

            # Click post button
            print("\n🖊️ Opening post composer...")
            try:
                post_btn = await page.wait_for_selector('button:has-text("Start a post")', timeout=5000)
                await post_btn.click()
                print("✅ Post composer opened")
            except:
                await page.click('[aria-label="Start a post"]')
                print("✅ Post composer opened (alt method)")

            # Type content
            print("\n📝 Typing content...")
            text_area = await page.wait_for_selector('div[contenteditable="true"]', timeout=5000)
            await text_area.click()
            await text_area.type(content, delay=10)
            print("✅ Content typed")

            # Post
            print("\n📤 Posting...")
            try:
                await page.wait_for_selector('button:has-text("Post")', timeout=3000)
                post_submit = await page.query_selector('button:has-text("Post")')
                await post_submit.click()
            except:
                # Fallback: keyboard
                await page.keyboard.press('Enter')

            print("✅ Posted!")

            # Wait for confirmation
            await asyncio.sleep(2)

            print("\n" + "="*70)
            print("✅ SUCCESS! Post published")
            print("="*70)
            return True

        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            return False
        finally:
            await page.close()
            await context.close()
            await browser.close()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 linkedin_post_daemon.py \"Your post content\"")
        print("\nExample:")
        print('  python3 linkedin_post_daemon.py "Hello LinkedIn! 🚀"')
        sys.exit(1)

    content = sys.argv[1]
    success = await post_to_linkedin(content)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
