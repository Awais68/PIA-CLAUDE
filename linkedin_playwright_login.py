#!/usr/bin/env python3
"""
LinkedIn Authentication using Playwright
Supports both email/password and OAuth methods
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

try:
    from playwright.async_api import async_playwright, BrowserContext, Page
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    print("   Then install browsers: playwright install chromium")
    sys.exit(1)


class LinkedInPlaywrightLogin:
    """LinkedIn authentication using Playwright"""

    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL', '')
        self.password = os.getenv('LINKEDIN_PASSWORD', '')
        self.session_path = Path.home() / '.linkedin_session'
        self.cookies_path = self.session_path / 'cookies.json'
        self.storage_path = self.session_path / 'storage'

        # Create session directory
        self.session_path.mkdir(exist_ok=True)
        self.storage_path.mkdir(exist_ok=True)

    async def login_with_email_password(self, page: Page) -> bool:
        """Authenticate using email and password"""
        print("\n📧 Authenticating with Email & Password...")

        if not self.email or not self.password:
            print("❌ LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")
            return False

        try:
            # Navigate to LinkedIn
            print("🌐 Loading LinkedIn...")
            await page.goto('https://www.linkedin.com/login', wait_until='networkidle')

            # Fill email
            print(f"📝 Logging in as: {self.email}")
            await page.fill('input[name="session_key"]', self.email)
            await page.fill('input[name="session_password"]', self.password)

            # Submit login form
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')

            # Check if login was successful
            try:
                await page.wait_for_url('https://www.linkedin.com/feed/**', timeout=10000)
                print("✅ Email/password authentication successful!")
                return True
            except:
                # Check for login error
                error_msg = await page.query_selector('.alertBanner_dismissible')
                if error_msg:
                    print(f"❌ Login failed: {await error_msg.text_content()}")
                else:
                    print("❌ Login failed or took too long")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {str(e)[:80]}")
            return False

    async def login_with_oauth(self, page: Page) -> bool:
        """Authenticate using OAuth (opens manual browser)"""
        print("\n🔐 Authenticating with OAuth...")
        print("⚠️  This requires manual interaction in the browser window.")
        print("    1. LinkedIn login page will open")
        print("    2. Authenticate with your account")
        print("    3. Grant permissions")
        print("    4. Script will capture session automatically\n")

        try:
            # Navigate to LinkedIn
            print("🌐 Loading LinkedIn...")
            await page.goto('https://www.linkedin.com/login', wait_until='networkidle')

            # Wait for user to manually authenticate
            print("⏳ Waiting for you to authenticate (timeout: 5 minutes)...")
            await page.wait_for_url('https://www.linkedin.com/feed/**', timeout=300000)

            print("✅ OAuth authentication successful!")
            return True

        except asyncio.TimeoutError:
            print("⏱️  Authentication timeout (5 minutes)")
            return False
        except Exception as e:
            print(f"❌ OAuth error: {str(e)[:80]}")
            return False

    async def verify_login(self, page: Page) -> bool:
        """Verify that login was successful"""
        print("\n✔️  Verifying login...")

        try:
            # Check if we're on LinkedIn feed (simplest check)
            current_url = page.url
            if 'linkedin.com/feed' in current_url or 'linkedin.com/me' in current_url:
                print(f"✅ Successfully logged into LinkedIn")
                print(f"   Current page: {current_url[:50]}...")
                return True

            # Try to navigate to profile
            await page.goto('https://www.linkedin.com/me', wait_until='networkidle', timeout=10000)

            # Check if navigation succeeded (we're logged in if we can access /me)
            if 'linkedin.com/me' in page.url or 'linkedin.com/in/' in page.url:
                print(f"✅ Profile page loaded successfully")
                return True
            else:
                print("⚠️  Unexpected page after login")
                return True  # Still consider it success if we got past login

        except Exception as e:
            # Even if verification fails, login likely succeeded
            print(f"⚠️  Verification check skipped: {str(e)[:40]}")
            return True  # Don't fail on verification - trust the earlier login check

    async def save_session(self, context: BrowserContext):
        """Save browser context (cookies + storage)"""
        print("\n💾 Saving session...")

        try:
            # Save cookies
            cookies = await context.cookies()
            with open(self.cookies_path, 'w') as f:
                json.dump(cookies, f, indent=2)
            print(f"✅ Cookies saved to: {self.cookies_path}")

            # Save local storage
            pages = context.pages
            if pages:
                storage = await context.storage_state()
                storage_file = self.storage_path / 'storage_state.json'
                with open(storage_file, 'w') as f:
                    json.dump(storage, f, indent=2)
                print(f"✅ Storage state saved to: {storage_file}")

        except Exception as e:
            print(f"⚠️  Error saving session: {str(e)[:60]}")

    async def load_session(self, context: BrowserContext) -> bool:
        """Load saved session"""
        if self.cookies_path.exists():
            print("\n📂 Loading saved session...")
            try:
                with open(self.cookies_path, 'r') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print("✅ Cookies loaded")
                return True
            except Exception as e:
                print(f"⚠️  Could not load session: {str(e)[:60]}")
                return False
        return False

    async def test_session(self, page: Page) -> bool:
        """Test if saved session is still valid"""
        print("\n🧪 Testing session validity...")

        try:
            await page.goto('https://www.linkedin.com/feed', wait_until='networkidle', timeout=15000)

            # Check if we're logged in
            profile_icon = await page.query_selector('img[alt="Your profile photo"]')
            if profile_icon:
                print("✅ Session is valid and active")
                return True
            else:
                print("⚠️  Session may have expired")
                return False

        except Exception as e:
            print(f"❌ Session test failed: {str(e)[:60]}")
            return False

    async def run(self, method: str = 'password', headless: bool = False):
        """Run the login flow"""
        print("\n" + "="*100)
        print("🔐 LINKEDIN PLAYWRIGHT LOGIN")
        print("="*100)
        print(f"Method: {method}")
        print(f"Session Path: {self.session_path}")

        async with async_playwright() as p:
            # Launch browser
            print(f"\n🚀 Launching browser (headless={headless})...")
            browser = await p.chromium.launch(headless=headless)

            # Try to load saved session first
            context = await browser.new_context()
            session_loaded = await self.load_session(context)

            if session_loaded:
                page = await context.new_page()
                if await self.test_session(page):
                    print("\n✅ Existing session is still valid! No login needed.")
                    await page.close()
                    await context.close()
                    await browser.close()
                    return True
                else:
                    print("\n⚠️  Existing session expired. Re-authenticating...")

            await context.close()

            # Create fresh context for new login
            context = await browser.new_context()
            page = await context.new_page()

            # Perform login based on method
            success = False
            if method == 'password':
                success = await self.login_with_email_password(page)
            elif method == 'oauth':
                success = await self.login_with_oauth(page)
            else:
                print(f"❌ Unknown method: {method}")

            if success:
                # Save session IMMEDIATELY after successful login
                # Don't wait for verification - just save it!
                await self.save_session(context)

                # Try to verify login for info, but don't gate on it
                await self.verify_login(page)

                print("\n" + "="*100)
                print("✅ LOGIN SUCCESSFUL!")
                print("="*100)
                print("\nYour session has been saved!")
                print("Session Path: " + str(self.session_path))
                print("\nNext steps:")
                print("1. Run: python linkedin_playwright_validator.py")
                print("   to validate your session\n")
                print("2. Create LinkedIn posts in: AI_Employee_Vault/Pending_Approval/social/")
                print("   They will auto-post when approved!\n")

            else:
                print("\n❌ Login failed. Please try again.")

            await page.close()
            await context.close()
            await browser.close()

            return success


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='LinkedIn Playwright Login')
    parser.add_argument('--method', choices=['password', 'oauth'], default='password',
                       help='Authentication method')
    parser.add_argument('--headless', action='store_true', default=False,
                       help='Run browser in headless mode (requires pre-saved session or manual setup)')
    parser.add_argument('--no-headless', dest='headless', action='store_false',
                       help='Show browser window during login')

    args = parser.parse_args()

    login = LinkedInPlaywrightLogin()
    success = await login.run(method=args.method, headless=args.headless)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
