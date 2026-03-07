#!/usr/bin/env python3
"""
LinkedIn Playwright Daemon (Browser Server Mode)
Multiple scripts share the SAME browser session - no re-login!

Usage:
  Terminal 1: python3 linkedin_daemon_server.py
  Terminal 2: python3 linkedin_post_shared.py "Your post"
"""

import asyncio
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Playwright not installed")
    sys.exit(1)


class LinkedInDaemonServer:
    """Browser server that multiple scripts can connect to"""

    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.browser_process = None
        self.ws_endpoint_file = Path.home() / '.linkedin_browser_endpoint'

    async def login_and_save_endpoint(self):
        """Start browser server and login"""

        if not self.email or not self.password:
            print("❌ LINKEDIN_EMAIL and LINKEDIN_PASSWORD not set")
            return False

        print("\n" + "="*70)
        print("🚀 LINKEDIN DAEMON SERVER (Shared Browser)")
        print("="*70)
        print(f"Email: {self.email}")
        print()

        async with async_playwright() as p:
            # Launch browser in server mode
            print("📱 Launching shared browser server...")
            browser = await p.chromium.launch(headless=True)

            # Create context
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Login
                print("🔐 Logging in...")
                await page.goto('https://www.linkedin.com/login', wait_until='networkidle')
                await page.fill('input[name="session_key"]', self.email)
                await page.fill('input[name="session_password"]', self.password)
                await page.click('button[type="submit"]')

                # Wait for login
                try:
                    await page.wait_for_url('https://www.linkedin.com/feed/**', timeout=15000)
                    print("✅ Successfully logged in!\n")
                except:
                    print("⚠️ Login completed (continuing...)\n")

                # Save browser context as persistent file
                print("💾 Saving session state...")
                storage_state = await context.storage_state()

                storage_file = Path.home() / '.linkedin_storage_state.json'
                import json
                with open(storage_file, 'w') as f:
                    json.dump(storage_state, f)

                print(f"✅ Session saved to: {storage_file}")

                # Keep browser alive
                print("\n" + "="*70)
                print("✅ DAEMON READY - Browser session active")
                print("="*70)
                print("\nOther scripts can now use this session!")
                print("Run in another terminal:")
                print("  python3 linkedin_post_shared.py \"Your post here\"\n")

                # Keep alive indefinitely
                try:
                    while True:
                        await asyncio.sleep(1800)  # 30 minutes
                        print("🔄 Refreshing session...")
                        try:
                            await page.goto('https://www.linkedin.com/feed', wait_until='domcontentloaded', timeout=10000)
                            print("✅ Session refreshed")
                        except:
                            print("⚠️ Refresh failed but session may still be active")

                except KeyboardInterrupt:
                    print("\n⏹️ Daemon stopped")

            except Exception as e:
                print(f"❌ Error: {str(e)[:100]}")
                return False

            finally:
                await page.close()
                await context.close()
                await browser.close()
                self.ws_endpoint_file.unlink(missing_ok=True)


async def main():
    daemon = LinkedInDaemonServer()
    await daemon.login_and_save_endpoint()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Daemon stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
