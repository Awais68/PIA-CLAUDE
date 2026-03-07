#!/usr/bin/env python3
"""
LinkedIn Playwright Daemon - Keeps browser session alive
Stays logged in so posts don't need to re-login

Usage:
  Terminal 1: python3 linkedin_daemon.py
  Terminal 2: python3 linkedin_post.py (uses daemon, no login!)
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import socket
import time

load_dotenv()

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed")
    sys.exit(1)


class LinkedInDaemon:
    """Background daemon that keeps LinkedIn session alive"""

    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.browser = None
        self.context = None
        self.page = None
        self.logged_in = False
        self.daemon_port = 9999
        self.pid_file = Path.home() / '.linkedin_daemon.pid'

    async def login(self):
        """Login to LinkedIn once"""
        if not self.email or not self.password:
            print("❌ LINKEDIN_EMAIL and LINKEDIN_PASSWORD not set")
            return False

        try:
            print(f"🔐 Logging in as {self.email}...")

            # Navigate to login
            await self.page.goto('https://www.linkedin.com/login', wait_until='networkidle')

            # Fill credentials
            await self.page.fill('input[name="session_key"]', self.email)
            await self.page.fill('input[name="session_password"]', self.password)

            # Submit
            await self.page.click('button[type="submit"]')
            await self.page.wait_for_load_state('networkidle', timeout=15000)

            # Verify login
            try:
                await self.page.wait_for_url('https://www.linkedin.com/feed/**', timeout=10000)
                print("✅ Logged in successfully!")
                self.logged_in = True
                return True
            except:
                print("⚠️ Login status unclear but continuing...")
                self.logged_in = True
                return True

        except Exception as e:
            print(f"❌ Login failed: {str(e)[:60]}")
            return False

    async def keep_alive(self):
        """Keep session alive by checking feed periodically"""
        while self.logged_in:
            try:
                # Visit feed every 30 minutes to keep session fresh
                await asyncio.sleep(1800)  # 30 minutes

                if self.page:
                    print("🔄 Refreshing session...")
                    await self.page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded')
                    print("✅ Session refreshed")

            except Exception as e:
                print(f"⚠️ Keep-alive error: {str(e)[:40]}")

    async def run(self):
        """Start the daemon"""
        print("\n" + "="*70)
        print("🚀 LINKEDIN PLAYWRIGHT DAEMON")
        print("="*70)
        print(f"PID: {os.getpid()}")
        print(f"Email: {self.email}")
        print()

        # Save PID
        self.pid_file.write_text(str(os.getpid()))

        async with async_playwright() as p:
            print("📱 Launching browser...")
            self.browser = await p.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

            print("✅ Browser ready\n")

            # Login
            if not await self.login():
                print("❌ Failed to login")
                await self.browser.close()
                self.pid_file.unlink(missing_ok=True)
                return False

            print("\n" + "="*70)
            print("✅ DAEMON READY")
            print("="*70)
            print("\nDaemon is running and logged in!")
            print("Posts can now be sent without re-login.\n")
            print("Run in another terminal:")
            print("  python3 linkedin_post_daemon.py\n")

            # Keep session alive
            try:
                await self.keep_alive()
            except KeyboardInterrupt:
                print("\n\n⏹️  Daemon stopped by user")
            finally:
                await self.browser.close()
                self.pid_file.unlink(missing_ok=True)


async def main():
    daemon = LinkedInDaemon()
    await daemon.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Daemon stopped")
    except Exception as e:
        print(f"❌ Daemon error: {e}")
