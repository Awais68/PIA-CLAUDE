#!/usr/bin/env python3
"""
Post to LinkedIn using daemon's saved session
No re-login needed!

Usage:
  python3 linkedin_post_shared.py "Your post content here"
"""

import asyncio
import sys
import json
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed")
    sys.exit(1)


async def post_to_linkedin(content: str) -> bool:
    """Post using daemon's saved session"""

    storage_file = Path.home() / '.linkedin_storage_state.json'

    if not storage_file.exists():
        print("❌ Session not found!")
        print("   Run daemon first: python3 linkedin_daemon_server.py")
        return False

    print("\n" + "="*70)
    print("📱 LINKEDIN POST (Using Shared Session)")
    print("="*70)
    print(f"Content: {content[:60]}...")
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Load saved session
        print("📂 Loading saved session...")
        with open(storage_file, 'r') as f:
            storage_state = json.load(f)

        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()

        try:
            # Open feed
            print("🌐 Opening LinkedIn feed...")
            await page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=10000)

            # Check if logged in
            print("✅ Checking login status...")
            await page.wait_for_selector('button:has-text("Start a post")', timeout=5000)

            # Click post button
            print("\n🖊️ Opening post composer...")
            post_btn = await page.query_selector('button:has-text("Start a post")')
            if post_btn:
                await post_btn.click()
            else:
                await page.click('[aria-label="Start a post"]')

            await asyncio.sleep(1)
            print("✅ Post composer opened")

            # Type content
            print("\n📝 Typing content...")
            text_area = await page.wait_for_selector('div[contenteditable="true"]', timeout=5000)
            await text_area.click()
            await text_area.type(content, delay=5)
            print("✅ Content typed")

            # Post
            print("\n📤 Posting...")
            try:
                post_submit = await page.query_selector('button:has-text("Post")')
                if post_submit:
                    await post_submit.click()
                else:
                    await page.keyboard.press('Enter')
            except:
                await page.keyboard.press('Enter')

            print("✅ Posted!")
            await asyncio.sleep(2)

            print("\n" + "="*70)
            print("✅ SUCCESS! Post published to LinkedIn")
            print("="*70)
            print("\nCheck your LinkedIn feed - post should be there!")
            return True

        except asyncio.TimeoutError:
            print("❌ Timeout - session may have expired")
            print("   Run daemon again: python3 linkedin_daemon_server.py")
            return False
        except Exception as e:
            print(f"❌ Error: {str(e)[:100]}")
            return False
        finally:
            await page.close()
            await context.close()
            await browser.close()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 linkedin_post_shared.py \"Your post content\"")
        print("\nExample:")
        print('  python3 linkedin_post_shared.py "Hello LinkedIn! 🚀"')
        sys.exit(1)

    content = sys.argv[1]
    success = await post_to_linkedin(content)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
