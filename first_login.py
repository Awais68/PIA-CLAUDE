"""
WhatsApp First-Time Login Script

This script handles the initial login to WhatsApp Web:
1. Launches browser in NON-headless mode so you can see and interact
2. Opens WhatsApp Web
3. Waits for you to scan the QR code with your phone
4. Detects when login is successful (chat list appears)
5. Saves the browser session for future use

Run this script ONLY ONCE before using the watcher.
After successful login, the watcher will use the saved session and run headless.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os


def first_login():
    """
    Perform first-time login to WhatsApp Web.

    Process:
    1. Load configuration from .env
    2. Launch visible browser
    3. Navigate to WhatsApp Web
    4. Wait for user to scan QR code
    5. Detect successful login (chat list appears)
    6. Save session
    7. Exit
    """

    # Load environment
    load_dotenv()

    session_path = Path(os.getenv("WHATSAPP_WATCHER_SESSION_PATH", "./whatsapp_session")).resolve()
    vault_path = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./AI_Employee_Vault")).resolve()

    print("=" * 70)
    print("WhatsApp Web First-Time Login")
    print("=" * 70)
    print()
    print("This script will:")
    print("1. Open a browser window (VISIBLE, not headless)")
    print("2. Navigate to WhatsApp Web")
    print("3. Wait for you to scan the QR code with your phone")
    print("4. Save your session for future use")
    print()
    print(f"Session will be saved to: {session_path}")
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

        # Launch browser in VISIBLE mode (headless=False)
        browser = playwright.chromium.launch(headless=False)

        # Create context without existing state (fresh login)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(120000)  # 2 minutes for manual actions

        print("[2/3] Opening WhatsApp Web...")
        page.goto("https://web.whatsapp.com", wait_until="networkidle")

        print()
        print("=" * 70)
        print("QR CODE SCANNER READY")
        print("=" * 70)
        print()
        print("1. A browser window has opened with WhatsApp Web")
        print("2. You should see a QR code")
        print("3. Use your phone to scan the QR code:")
        print("   - Open WhatsApp on your phone")
        print("   - Go to Settings > Linked Devices")
        print("   - Tap 'Link a Device'")
        print("   - Scan the QR code displayed in the browser")
        print()
        print("4. Wait for the chat list to appear in the browser")
        print("   (this may take 30-60 seconds)")
        print()
        print("The script will automatically detect successful login...")
        print()

        # Wait for login to complete (chat list appears)
        print("[3/3] Waiting for login confirmation...")
        print("      (watching for chat list to load...)")

        max_wait = 120  # seconds
        wait_interval = 2
        elapsed = 0

        while elapsed < max_wait:
            try:
                # Check if chat list is visible (indicates successful login)
                chat_list = page.query_selector('[data-testid="pane-side"]')

                if chat_list:
                    # Additional check: make sure at least one chat is visible
                    chats = page.query_selector_all('[data-testid="chat"]')
                    if chats:
                        print()
                        print("✓ Login successful! Chat list detected.")
                        print(f"  Found {len(chats)} chat(s)")
                        break

            except Exception as e:
                pass  # Keep waiting

            time.sleep(wait_interval)
            elapsed += wait_interval
            dots = "." * ((elapsed // 5) % 4)
            print(f"\r      (watching for chat list to load...{dots})", end="", flush=True)

        if elapsed >= max_wait:
            print()
            print()
            print("⚠ Timeout: Chat list did not appear within 2 minutes")
            print()
            print("This could mean:")
            print("  - QR code scan failed or wasn't completed")
            print("  - Network connection issue")
            print("  - WhatsApp Web is having issues")
            print()
            print("The browser remains open. You can:")
            print("  1. Try scanning the QR code again")
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

            import json
            with open(state_file, 'w') as f:
                json.dump(state, f)

            print(f"✓ Session saved to: {state_file}")

        except Exception as e:
            print(f"⚠ Warning: Could not save session state: {e}")
            print("  This might be okay, but you may need to login again next time")

        print()
        print("=" * 70)
        print("LOGIN COMPLETE!")
        print("=" * 70)
        print()
        print("Your WhatsApp Web session has been saved.")
        print()
        print("You can now:")
        print("  1. Close this browser window")
        print("  2. Start the WhatsApp Watcher (it will run headless)")
        print()
        print("Command to start watcher:")
        print("  python whatsapp_watcher.py")
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
        print("  2. Try again: python first_login.py")
        print("  3. If problems persist, check WhatsApp Web is accessible")
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
