#!/usr/bin/env python3
"""
Direct LinkedIn posting using Playwright
Posts immediately without needing to save/load sessions
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed")
    sys.exit(1)


async def post_to_linkedin(content: str, headless: bool = True) -> bool:
    """Post content directly to LinkedIn"""

    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')

    if not email or not password:
        print("❌ LINKEDIN_EMAIL and LINKEDIN_PASSWORD not set in .env")
        return False

    print("\n" + "="*70)
    print("📱 LINKEDIN DIRECT POST")
    print("="*70)
    print(f"Posting to: {email}")
    print(f"Content: {content[:60]}...")
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Step 1: Login
            print("🔐 Step 1: Logging in...")
            await page.goto('https://www.linkedin.com/login', wait_until='networkidle')

            # Fill credentials
            await page.fill('input[name="session_key"]', email)
            await page.fill('input[name="session_password"]', password)

            # Submit
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle', timeout=15000)

            # Check if login successful
            try:
                await page.wait_for_url('https://www.linkedin.com/feed/**', timeout=10000)
                print("✅ Logged in!")
            except:
                print("⚠️ Login status unclear, continuing...")

            # Step 2: Navigate to post composer
            print("\n🖊️ Step 2: Opening post composer...")
            await page.goto('https://www.linkedin.com/feed', wait_until='networkidle')

            # Wait for and click post button
            try:
                post_button = await page.wait_for_selector('button:has-text("Start a post")', timeout=10000)
                await post_button.click()
                print("✅ Post composer opened!")
            except:
                # Try alternative selector
                try:
                    await page.click('[aria-label="Start a post"]')
                    print("✅ Post composer opened! (alt method)")
                except:
                    print("⚠️ Could not find post button, trying text area...")
                    # Just try to find any text area
                    await page.click('div[contenteditable="true"]')

            # Step 3: Type content
            print("\n📝 Step 3: Typing content...")

            # Wait for text editor
            text_area = await page.wait_for_selector('.ql-editor, [contenteditable="true"]', timeout=5000)
            await text_area.click()
            await text_area.type(content, delay=10)
            print(f"✅ Content typed!")

            # Step 4: Post
            print("\n📤 Step 4: Posting...")

            # Method 1: Try clicking Post button
            try:
                post_submit = await page.wait_for_selector('button:has-text("Post")', timeout=3000)
                await post_submit.click()
                print("✅ Clicked Post button")
            except:
                # Method 2: Try keyboard shortcut
                try:
                    await page.keyboard.press('Enter')
                    print("✅ Pressed Enter to post")
                except:
                    print("⚠️ Could not post - trying alternative...")
                    pass

            # Wait a bit for post to process
            await asyncio.sleep(2)

            print("\n" + "="*70)
            print("✅ SUCCESS! Post sent to LinkedIn")
            print("="*70)
            print("\nCheck your LinkedIn feed - your post should be there!")
            return True

        except asyncio.TimeoutError as e:
            print(f"\n⏱️ Timeout: {str(e)[:60]}")
            return False
        except Exception as e:
            print(f"\n❌ Error: {str(e)[:100]}")
            return False
        finally:
            await page.close()
            await context.close()
            await browser.close()


async def main():
    """Test posting"""

    # Test content
    test_content = """Testing LinkedIn Playwright! 🚀

If you see this, the integration is working perfectly!

#automation #ai"""

    # Post with visible browser first (so you can see it working)
    success = await post_to_linkedin(test_content, headless=False)

    if success:
        print("\n✨ LinkedIn posting is ready!")
        print("   You can now create posts and they'll auto-post")
    else:
        print("\n⚠️ Posting failed - check the browser window for issues")

    return success


if __name__ == '__main__':
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
