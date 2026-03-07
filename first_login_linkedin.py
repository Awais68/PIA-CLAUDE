"""
LinkedIn First-Time Login Script

This script handles the initial login to LinkedIn:
1. Launches browser in NON-headless mode (visible)
2. Opens LinkedIn.com
3. Waits for user to manually login
4. Detects when login is successful (feed page loaded)
5. Saves browser session for future use

Run this script ONLY ONCE before using the watcher or poster.
After successful login, the watcher will use the saved session and run headless.
"""

import sys
import time
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os


def first_login():
    """
    Perform first-time login to LinkedIn.

    Process:
    1. Load configuration from .env
    2. Launch visible browser
    3. Navigate to LinkedIn login
    4. Wait for user to login manually
    5. Detect successful login (feed page loaded)
    6. Save session
    7. Exit
    """

    # Load environment
    load_dotenv()

    session_path = Path(os.getenv("LINKEDIN_SESSION_PATH", "./linkedin_session")).resolve()
    vault_path = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./AI_Employee_Vault")).resolve()

    print("=" * 70)
    print("LinkedIn First-Time Login")
    print("=" * 70)
    print()
    print("This script will:")
    print("1. Open a browser window (VISIBLE, not headless)")
    print("2. Navigate to LinkedIn.com")
    print("3. Wait for you to manually login")
    print("4. Save your session for future use")
    print()
    print(f"Session will be saved to: {session_path}")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Use your actual LinkedIn email & password")
    print("   - Complete any 2FA if prompted")
    print("   - Do NOT close the browser - let the script detect login")
    print()
    print("Press Enter to continue, or Ctrl+C to cancel...")
    input()

    playwright = None
    browser = None
    context = None
    page = None

    try:
        print("\n[1/3] Starting browser (visible mode)...")
        playwright = sync_playwright().start()

        # Create session directory
        session_path.mkdir(parents=True, exist_ok=True)

        # Launch browser in VISIBLE mode
        browser = playwright.chromium.launch(headless=False)

        # Create context without existing state (fresh login)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(120000)  # 2 minutes

        print("[2/3] Opening LinkedIn.com...")
        page.goto("https://www.linkedin.com/login", wait_until="networkidle")

        print()
        print("=" * 70)
        print("LOGIN REQUIRED")
        print("=" * 70)
        print()
        print("A browser window has opened with LinkedIn login page.")
        print()
        print("Please:")
        print("  1. Enter your LinkedIn email")
        print("  2. Click 'Sign in'")
        print("  3. Enter your password")
        print("  4. Complete any security checks (2FA, CAPTCHA, etc.)")
        print("  5. Wait for your feed to load")
        print()
        print("The script will automatically detect successful login...")
        print()

        # Wait for login to complete (feed loads)
        print("[3/3] Waiting for login confirmation...")
        print("      (watching for feed to load...)")

        max_wait = 300  # 5 minutes
        wait_interval = 2
        elapsed = 0

        while elapsed < max_wait:
            try:
                # Check if feed is visible (indicates successful login)
                feed = page.query_selector('[data-test-id="feed"]')

                if feed:
                    # Additional check: wait for at least one post to load
                    posts = page.query_selector_all('[data-test-id="feed-post-item"]')
                    if posts:
                        print()
                        print("✓ Login successful! Feed detected.")
                        print(f"  Found {len(posts)} post(s)")
                        break

                # Also check for alternative selectors
                if page.url.startswith("https://www.linkedin.com/feed/"):
                    print()
                    print("✓ Login successful! Feed page loaded.")
                    break

            except Exception as e:
                pass  # Keep waiting

            time.sleep(wait_interval)
            elapsed += wait_interval
            dots = "." * ((elapsed // 5) % 4)
            print(f"\r      (watching for feed to load...{dots})", end="", flush=True)

        if elapsed >= max_wait:
            print()
            print()
            print("⚠ Timeout: Feed did not load within 5 minutes")
            print()
            print("This could mean:")
            print("  - Login was not completed")
            print("  - Network connection issue")
            print("  - LinkedIn is having issues")
            print("  - 2FA/CAPTCHA is still pending")
            print()
            print("The browser remains open. You can:")
            print("  1. Complete the login process")
            print("  2. Refresh the page (F5)")
            print("  3. Close the browser and try again")
            print()
            input("Press Enter when ready to close...")
            return False

        print()
        print()

        # Save session state
        print("Saving session...")
        try:
            state = context.storage_state()
            state_file = session_path / "state.json"

            with open(state_file, 'w') as f:
                json.dump(state, f)

            print(f"✓ Session saved to: {state_file}")

        except Exception as e:
            print(f"⚠ Warning: Could not save session state: {e}")
            print("  This might be okay, but you may need to login again next time")

        # Get basic profile info
        try:
            profile_name_elem = page.query_selector('[data-test-id="user-name"]')
            if profile_name_elem:
                profile_name = profile_name_elem.inner_text()
                print(f"✓ Logged in as: {profile_name}")
        except:
            pass

        print()
        print("=" * 70)
        print("LOGIN COMPLETE!")
        print("=" * 70)
        print()
        print("Your LinkedIn session has been saved.")
        print()
        print("You can now:")
        print("  1. Close this browser window")
        print("  2. Start the LinkedIn Watcher (monitors DMs, comments, visitors)")
        print("  3. Start the LinkedIn Poster (auto-posts approved content)")
        print()
        print("Commands to start:")
        print("  python3 linkedin_watcher.py")
        print("  python3 linkedin_poster.py")
        print()
        print("Press Enter to close the browser and exit...")
        input()

        return True

    except KeyboardInterrupt:
        print()
        print()
        print("⚠ Login cancelled by user")
        return False

    except Exception as e:
        print()
        print()
        print(f"✗ Error during login: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure you have internet connection")
        print("  2. Try again: python3 first_login_linkedin.py")
        print("  3. If problems persist, check LinkedIn is accessible")
        print("  4. Check browser console for errors (F12)")
        print()
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        try:
            if page:
                page.close()
            if context:
                context.close()
            if browser:
                browser.close()
            if playwright:
                playwright.stop()
        except Exception as e:
            print(f"Note: {e}")


if __name__ == "__main__":
    success = first_login()
    sys.exit(0 if success else 1)
