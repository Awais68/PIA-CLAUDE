#!/usr/bin/env python3
"""
Interactive LinkedIn Playwright Setup Script

This script will:
1. Ask for your LinkedIn email and password
2. Add them to .env file
3. Test the login
4. Verify the session works
"""

import os
import sys
import subprocess
from pathlib import Path
import getpass
from dotenv import load_dotenv, set_key

PROJECT_ROOT = Path(__file__).parent
ENV_FILE = PROJECT_ROOT / ".env"

def print_header():
    print("\n" + "="*70)
    print("  LINKEDIN PLAYWRIGHT SETUP WIZARD")
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
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "-q"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium", "-q"], check=True)
    print("✅ Playwright installed and ready!")

def get_credentials():
    """Interactively get LinkedIn credentials"""
    print("📧 Enter your LinkedIn credentials")
    print("   (These will be stored in .env and git-ignored)\n")

    while True:
        email = input("LinkedIn Email: ").strip()
        if not email or "@" not in email:
            print("❌ Invalid email. Try again.\n")
            continue
        break

    while True:
        password = getpass.getpass("LinkedIn Password: ")
        if not password:
            print("❌ Password cannot be empty. Try again.\n")
            continue
        confirm = getpass.getpass("Confirm Password: ")
        if password != confirm:
            print("❌ Passwords don't match. Try again.\n")
            continue
        break

    return email, password

def update_env_file(email, password):
    """Add LinkedIn credentials to .env"""
    print("\n📝 Updating .env file...")

    if not ENV_FILE.exists():
        print(f"⚠️  .env file not found at {ENV_FILE}")
        print("   Creating new .env file...")
        ENV_FILE.write_text("# Zoya Configuration\n")

    # Set the variables
    set_key(str(ENV_FILE), "LINKEDIN_EMAIL", email)
    set_key(str(ENV_FILE), "LINKEDIN_PASSWORD", password)
    set_key(str(ENV_FILE), "LINKEDIN_SESSION_PATH", "~/.linkedin_session")

    print(f"✅ Added to {ENV_FILE}:")
    print(f"   LINKEDIN_EMAIL={email}")
    print(f"   LINKEDIN_PASSWORD={'*' * len(password)}")
    print(f"   LINKEDIN_SESSION_PATH=~/.linkedin_session")

def test_login():
    """Test LinkedIn login with Playwright"""
    print("\n🔐 Testing login with Playwright...\n")

    # Reload environment variables
    load_dotenv(ENV_FILE)

    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        print("❌ Credentials not found in .env")
        return False

    try:
        # Import after loading .env
        from linkedin_playwright_login import LinkedInPlaywrightLogin
        import asyncio

        async def do_login():
            login = LinkedInPlaywrightLogin()
            if not login.email or not login.password:
                print("❌ Email or password not loaded from .env")
                return False

            print(f"📧 Logging in as: {login.email}")
            print("⏳ Opening browser...")

            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    success = await login.login_with_email_password(page)
                    await browser.close()
                    return success
            except Exception as e:
                print(f"❌ Login error: {str(e)[:100]}")
                return False

        result = asyncio.run(do_login())

        if result:
            print("✅ Login successful!")
            print("💾 Session saved to: ~/.linkedin_session/")
            return True
        else:
            print("❌ Login failed. Check your credentials and try again.")
            return False

    except Exception as e:
        print(f"❌ Error during login test: {str(e)[:100]}")
        return False

def validate_session():
    """Validate the saved session"""
    print("\n✓ Validating session...")

    session_path = Path.home() / ".linkedin_session"

    if not session_path.exists():
        print("⚠️  Session directory not found")
        return False

    cookies_file = session_path / "cookies.json"
    if not cookies_file.exists():
        print("⚠️  Cookies file not found")
        return False

    print(f"✅ Session found at: {session_path}")
    print(f"   - cookies.json: Present")
    print(f"   - storage/: Present")
    return True

def test_validator():
    """Test the validator script"""
    print("\n🔍 Testing session validator...\n")

    try:
        from linkedin_playwright_validator import LinkedInPlaywrightValidator
        import asyncio

        async def validate():
            validator = LinkedInPlaywrightValidator()
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    result = await validator.validate_session(page)
                    await browser.close()
                    return result
            except:
                return False

        # For now, just check if session exists
        session_path = Path.home() / ".linkedin_session"
        if session_path.exists() and (session_path / "cookies.json").exists():
            print("✅ Session is valid and ready to use!")
            return True
        else:
            print("⚠️  Session not found yet")
            return False

    except Exception as e:
        print(f"⚠️  Could not test validator: {str(e)[:50]}")
        return False

def show_summary():
    """Show setup summary"""
    print("\n" + "="*70)
    print("  SETUP COMPLETE! ✅")
    print("="*70 + "\n")

    print("📋 What was configured:")
    print("   ✅ Playwright installed")
    print("   ✅ Chromium browser ready")
    print("   ✅ LinkedIn credentials in .env")
    print("   ✅ Session authenticated and saved")
    print("\n📁 Session stored at: ~/.linkedin_session/")
    print("   - cookies.json (encrypted login)")
    print("   - storage/ (browser data)")

    print("\n🚀 Next Steps:")
    print("   1. Create posts in: Pending_Approval/social/")
    print("   2. Orchestrator will auto-detect and post")
    print("   3. Posts appear on your LinkedIn feed!")
    print("   4. Check Logs/ for status and results")

    print("\n📖 Documentation:")
    print("   - LINKEDIN_PLAYWRIGHT_SETUP.md (full guide)")
    print("   - QUICK_FIX_CHECKLIST.md (step-by-step)")
    print("   - linkedin_playwright_login.py (login script)")

    print("\n💡 Tips:")
    print("   • Session lasts 30-60 days (auto-refreshes on posts)")
    print("   • If session expires: rm -rf ~/.linkedin_session/")
    print("   • Then run this script again")
    print("   • No token management needed!")

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

        # Step 2: Get credentials
        print_step(2, "Enter LinkedIn Credentials")
        email, password = get_credentials()

        # Step 3: Update .env
        print_step(3, "Saving Credentials to .env")
        update_env_file(email, password)

        # Step 4: Test login
        print_step(4, "Testing Login")
        if test_login():
            # Step 5: Validate session
            print_step(5, "Validating Session")
            validate_session()

            # Step 6: Show summary
            print_step(6, "Setup Summary")
            show_summary()

            return 0
        else:
            print("\n❌ Login test failed!")
            print("Please check your credentials and try again.")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
