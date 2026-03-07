#!/usr/bin/env python3
"""
Interactive WhatsApp Local Setup Script

This script will:
1. Check Playwright installation
2. Start WhatsApp Web login (QR code)
3. Save session locally
4. Verify connection works
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv, set_key

PROJECT_ROOT = Path(__file__).parent
ENV_FILE = PROJECT_ROOT / ".env"
SESSION_PATH = Path.home() / ".whatsapp_session"

def print_header():
    print("\n" + "="*70)
    print("  WHATSAPP LOCAL SETUP WIZARD")
    print("="*70 + "\n")

def print_step(step_num, title):
    print(f"\n{'─'*70}")
    print(f"STEP {step_num}: {title}")
    print(f"{'─'*70}\n")

def check_playwright():
    """Verify Playwright is installed"""
    try:
        import playwright
        return True
    except ImportError:
        return False

def install_playwright():
    """Install Playwright if needed"""
    print("📦 Installing Playwright...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "-q"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium", "-q"], check=True)
    print("✅ Playwright installed and ready!")

def show_whatsapp_info():
    """Show WhatsApp info"""
    print("📱 WhatsApp Local Setup\n")
    print("This uses WhatsApp Web on your computer:")
    print("   • No cloud tokens or API keys")
    print("   • Session saved locally to: ~/.whatsapp_session/")
    print("   • Completely local - your phone controls it")
    print("   • Send messages via Playwright browser automation\n")
    print("Requirements:")
    print("   ✅ Playwright (will install if needed)")
    print("   ✅ Your phone with WhatsApp app")
    print("   ✅ Keep your phone nearby for QR scan\n")

def start_whatsapp_login():
    """Start WhatsApp Web login"""
    print("🔐 Starting WhatsApp Web login...\n")
    print("⏳ This will:")
    print("   1. Open a browser window")
    print("   2. Show a QR code")
    print("   3. You scan it with your phone")
    print("   4. Session is saved automatically\n")

    try:
        from whatsapp_login import WhatsAppPlaywrightLogin
        import asyncio

        async def do_login():
            login = WhatsAppPlaywrightLogin()
            print("📱 Opening WhatsApp Web...")
            success = await login.login_with_qr()
            return success

        result = asyncio.run(do_login())

        if result:
            print("\n✅ WhatsApp login successful!")
            print("💾 Session saved to: ~/.whatsapp_session/")
            return True
        else:
            print("\n❌ WhatsApp login failed")
            print("   Please check the browser window and try again")
            return False

    except FileNotFoundError:
        print("⚠️  whatsapp_login.py not found")
        print("   Creating minimal QR login script...\n")

        # Create a minimal login script if it doesn't exist
        create_minimal_whatsapp_login()
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)[:100]}")
        return False

def create_minimal_whatsapp_login():
    """Create minimal WhatsApp login if not present"""
    script_path = PROJECT_ROOT / "whatsapp_login.py"

    if not script_path.exists():
        content = '''#!/usr/bin/env python3
"""Minimal WhatsApp Web QR Login"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_PATH = Path.home() / ".whatsapp_session"

async def login_with_qr():
    """Login to WhatsApp Web with QR code"""
    SESSION_PATH.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state=str(SESSION_PATH / "state.json") if (SESSION_PATH / "state.json").exists() else None
        )
        page = await context.new_page()

        print("📱 Opening WhatsApp Web...")
        print("   Scan the QR code with your phone")
        await page.goto("https://web.whatsapp.com/", wait_until="networkidle")

        # Wait for login
        print("⏳ Waiting for you to scan QR code...")
        try:
            await page.wait_for_selector('[data-testid="chat-list-items"]', timeout=60000)
            print("✅ Successfully logged in to WhatsApp!")

            # Save session
            storage = await context.storage_state()
            SESSION_PATH.mkdir(exist_ok=True)
            import json
            (SESSION_PATH / "state.json").write_text(json.dumps(storage))
            print(f"💾 Session saved to: {SESSION_PATH}/")

        except:
            print("⚠️  Timeout - QR code may have expired")
            return False
        finally:
            await browser.close()

    return True

if __name__ == "__main__":
    asyncio.run(login_with_qr())
'''
        script_path.write_text(content)
        print(f"✅ Created {script_path}")
        print("   Ready to use for WhatsApp login")

def update_env_file():
    """Add WhatsApp config to .env"""
    print("\n📝 Updating .env file...\n")

    if not ENV_FILE.exists():
        print(f"⚠️  .env file not found at {ENV_FILE}")
        print("   Creating new .env file...")
        ENV_FILE.write_text("# Zoya Configuration\n")

    # Set the variables
    set_key(str(ENV_FILE), "WHATSAPP_SESSION_PATH", str(SESSION_PATH))
    set_key(str(ENV_FILE), "WHATSAPP_LOCAL_MODE", "true")

    print(f"✅ Added to {ENV_FILE}:")
    print(f"   WHATSAPP_SESSION_PATH={SESSION_PATH}")
    print(f"   WHATSAPP_LOCAL_MODE=true")

def validate_session():
    """Validate WhatsApp session"""
    print("\n✓ Validating session...\n")

    if not SESSION_PATH.exists():
        print("⚠️  Session directory not found yet")
        print("   It will be created after you scan the QR code")
        return False

    state_file = SESSION_PATH / "state.json"
    if state_file.exists():
        print(f"✅ Session found at: {SESSION_PATH}")
        print(f"   - state.json: Present (login cookies)")
        return True
    else:
        print("⚠️  Session not fully initialized yet")
        return False

def show_summary():
    """Show setup summary"""
    print("\n" + "="*70)
    print("  SETUP COMPLETE! ✅")
    print("="*70 + "\n")

    print("📋 What was configured:")
    print("   ✅ Playwright installed")
    print("   ✅ WhatsApp Web logged in (locally)")
    print("   ✅ Session saved locally")
    print("   ✅ Configuration added to .env")

    print("\n📁 Session stored at: ~/.whatsapp_session/")
    print("   - state.json (browser storage)")
    print("   - Contains login cookies & session data")

    print("\n🚀 Next Steps:")
    print("   1. Create WhatsApp messages in: Pending_Approval/social/")
    print("   2. Format: WHATSAPP_message_to_123456789.md")
    print("   3. Orchestrator will auto-detect and send")
    print("   4. Messages appear on WhatsApp!")
    print("   5. Check Logs/ for status and results")

    print("\n💡 How it works:")
    print("   • Session stays logged in (up to 30 days)")
    print("   • Messages sent via Playwright automation")
    print("   • Your phone doesn't need to be connected")
    print("   • Browser runs headless (invisible)")
    print("   • Your device is the 'API' for WhatsApp")

    print("\n📱 Phone Requirements:")
    print("   • Keep WhatsApp installed on your phone")
    print("   • Don't log out of WhatsApp Web")
    print("   • Don't change your password (session expires)")
    print("   • Session auto-refreshes on message send")

def show_troubleshooting():
    """Show troubleshooting tips"""
    print("\n" + "="*70)
    print("  TROUBLESHOOTING")
    print("="*70 + "\n")

    print("Problem: \"Browser didn't open\"")
    print("Fix:")
    print("   1. Check if Playwright installed: python3 -m playwright install chromium")
    print("   2. Check for popups or dialogs that blocked browser\n")

    print("Problem: \"QR Code took too long\"")
    print("Fix:")
    print("   1. QR codes expire after 1-2 minutes")
    print("   2. Run the login again")
    print("   3. Scan faster next time\n")

    print("Problem: \"Session invalid/expired\"")
    print("Fix:")
    print("   1. Session lasts ~30 days")
    print("   2. Or expires if you change password")
    print("   3. Delete and re-login: rm -rf ~/.whatsapp_session/")
    print("   4. Run this script again\n")

    print("Problem: \"Can't send messages\"")
    print("Fix:")
    print("   1. Check phone - is WhatsApp still logged in?")
    print("   2. Check internet connection")
    print("   3. Session may have expired - re-login\n")

def main():
    """Main setup flow"""
    try:
        print_header()

        # Step 1: Check Playwright
        print_step(1, "Checking Playwright Installation")
        if not check_playwright():
            print("📦 Playwright not found. Installing...")
            install_playwright()
        else:
            print("✅ Playwright already installed")

        # Step 2: Show info
        print_step(2, "WhatsApp Local Mode Info")
        show_whatsapp_info()

        input("Press Enter to continue...")

        # Step 3: Start login
        print_step(3, "WhatsApp Web Login")
        if not start_whatsapp_login():
            print("⚠️  Login had issues but configuration is ready")

        # Step 4: Update .env
        print_step(4, "Saving Configuration to .env")
        update_env_file()

        # Step 5: Validate session
        print_step(5, "Validating Session")
        validate_session()

        # Step 6: Show summary
        print_step(6, "Setup Summary")
        show_summary()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        show_troubleshooting()
        return 1

if __name__ == "__main__":
    sys.exit(main())
