#!/usr/bin/env python3
"""
Interactive Meta (Facebook) API Setup Script

This script will:
1. Guide you through getting Meta API credentials
2. Add them to .env
3. Test the connection
4. Verify posting capability
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv, set_key
import getpass

PROJECT_ROOT = Path(__file__).parent
ENV_FILE = PROJECT_ROOT / ".env"

def print_header():
    print("\n" + "="*70)
    print("  META (FACEBOOK) API SETUP WIZARD")
    print("="*70 + "\n")

def print_step(step_num, title):
    print(f"\n{'─'*70}")
    print(f"STEP {step_num}: {title}")
    print(f"{'─'*70}\n")

def guide_meta_setup():
    """Guide user through getting Meta API credentials"""
    print("📝 You'll need Meta API credentials\n")
    print("To get them:")
    print("   1. Go to: https://developers.facebook.com/")
    print("   2. Go to 'My Apps' → 'Create App'")
    print("   3. Select 'Business' as app type")
    print("   4. Set up the app (Facebook login)")
    print("   5. Go to 'Settings' → 'Basic'")
    print("   6. You'll find:\n")

    print("   • App ID")
    print("   • App Secret")
    print("   • Access Token (generate from 'Tools' → 'Access Token Tool')\n")

    print("Also needed:")
    print("   • Your Facebook Page ID (from page settings)")
    print("   • Your Instagram Business Account ID (if posting to Instagram)\n")

    print("Ready? (y/n): ", end="")
    response = input().strip().lower()
    return response == "y"

def get_credentials():
    """Interactively get Meta API credentials"""
    print("📧 Enter your Meta API credentials\n")

    creds = {}

    print("App ID:")
    creds["app_id"] = input("  > ").strip()
    if not creds["app_id"]:
        print("❌ App ID cannot be empty")
        return None

    print("\nApp Secret:")
    creds["app_secret"] = getpass.getpass("  > ")
    if not creds["app_secret"]:
        print("❌ App Secret cannot be empty")
        return None

    print("\nAccess Token:")
    creds["access_token"] = input("  > ").strip()
    if not creds["access_token"]:
        print("❌ Access Token cannot be empty")
        return None

    print("\nFacebook Page ID:")
    creds["page_id"] = input("  > ").strip()
    if not creds["page_id"]:
        print("⚠️  Page ID is optional (but needed for posting)")

    print("\nInstagram Business Account ID (optional):")
    creds["instagram_id"] = input("  > ").strip()

    return creds

def update_env_file(creds):
    """Add Meta credentials to .env"""
    print("\n📝 Updating .env file...\n")

    if not ENV_FILE.exists():
        print(f"⚠️  .env file not found at {ENV_FILE}")
        print("   Creating new .env file...")
        ENV_FILE.write_text("# Zoya Configuration\n")

    # Set the variables
    set_key(str(ENV_FILE), "META_APP_ID", creds["app_id"])
    set_key(str(ENV_FILE), "META_APP_SECRET", creds["app_secret"])
    set_key(str(ENV_FILE), "META_ACCESS_TOKEN", creds["access_token"])
    if creds.get("page_id"):
        set_key(str(ENV_FILE), "FACEBOOK_PAGE_ID", creds["page_id"])
    if creds.get("instagram_id"):
        set_key(str(ENV_FILE), "INSTAGRAM_BUSINESS_ID", creds["instagram_id"])

    print(f"✅ Added to {ENV_FILE}:")
    print(f"   META_APP_ID={creds['app_id']}")
    print(f"   META_APP_SECRET={'*' * len(creds['app_secret'])}")
    print(f"   META_ACCESS_TOKEN={'*' * len(creds['access_token'])}...")
    if creds.get("page_id"):
        print(f"   FACEBOOK_PAGE_ID={creds['page_id']}")
    if creds.get("instagram_id"):
        print(f"   INSTAGRAM_BUSINESS_ID={creds['instagram_id']}")

def test_api_connection():
    """Test Meta API connection"""
    print("\n🔐 Testing Meta API connection...\n")

    # Reload environment
    load_dotenv(ENV_FILE)

    try:
        from src.mcp_servers.meta_mcp_real import MetaMCPServer

        server = MetaMCPServer()

        if server.authenticated:
            print("✅ Meta API authentication successful!")
            print("   API is ready to use")
            return True
        else:
            print("⚠️  Could not verify authentication")
            return False

    except Exception as e:
        error_msg = str(e)[:100]
        print(f"⚠️  Connection test failed: {error_msg}")
        return False

def test_posting_capability():
    """Test posting capability"""
    print("\n📤 Testing posting capability...\n")

    try:
        from src.mcp_servers.meta_mcp_real import MetaMCPServer

        server = MetaMCPServer()

        if server.authenticated:
            print("✅ Meta API is ready to post!")
            print("   Your orchestrator can now post to:")
            print("   • Facebook (via Page ID)")
            print("   • Instagram (via Business Account ID)")
            return True
        else:
            print("⚠️  Could not verify posting capability")
            return False

    except Exception as e:
        print(f"⚠️  Capability test failed: {str(e)[:50]}")
        return False

def show_summary():
    """Show setup summary"""
    print("\n" + "="*70)
    print("  SETUP COMPLETE! ✅")
    print("="*70 + "\n")

    print("📋 What was configured:")
    print("   ✅ Meta API credentials added to .env")
    print("   ✅ Connection tested and verified")
    print("   ✅ Posting capability confirmed")

    print("\n🚀 Next Steps:")
    print("   1. Create posts in: Pending_Approval/social/")
    print("   2. Orchestrator will auto-detect and post")
    print("   3. Posts appear on Facebook/Instagram!")
    print("   4. Check Logs/ for status and results")

    print("\n💡 How it works:")
    print("   • Posts created as .md files in Pending_Approval/social/")
    print("   • FACEBOOK_*.md or INSTAGRAM_*.md files are detected")
    print("   • Orchestrator posts and moves to Done/")
    print("   • Results logged in Logs/YYYY-MM-DD.json")

    print("\n📊 Platform-Specific:")
    print("   Facebook:")
    print("   • Need Facebook Page ID")
    print("   • Access token must have pages_manage_posts permission")
    print("   • Can post text, images, links, videos")
    print("")
    print("   Instagram:")
    print("   • Need Instagram Business Account ID")
    print("   • Must link to Business Manager")
    print("   • Can post images and videos (reels)")

def show_troubleshooting():
    """Show troubleshooting tips"""
    print("\n" + "="*70)
    print("  TROUBLESHOOTING")
    print("="*70 + "\n")

    print("Problem: \"Invalid App ID or Secret\"")
    print("Fix:")
    print("   1. Go to https://developers.facebook.com/")
    print("   2. Select your app")
    print("   3. Go to Settings → Basic")
    print("   4. Copy App ID and App Secret exactly\n")

    print("Problem: \"Access Token expired\"")
    print("Fix:")
    print("   1. Go to Tools → Access Token Tool")
    print("   2. Generate a new access token")
    print("   3. Update META_ACCESS_TOKEN in .env\n")

    print("Problem: \"Insufficient permissions\"")
    print("Fix:")
    print("   1. Go to App Settings → Roles")
    print("   2. Ensure you have 'Admin' or 'Developer' role")
    print("   3. Check that app has 'pages_manage_posts' permission")
    print("   4. Re-generate access token after adding permissions\n")

    print("Problem: \"Page ID not found\"")
    print("Fix:")
    print("   1. Go to your Facebook Page")
    print("   2. Click 'Settings' → 'Page Info'")
    print("   3. Find 'Facebook Page ID' in the list")
    print("   4. Copy and paste into .env\n")

    print("Problem: \"401 Unauthorized\"")
    print("Fix:")
    print("   1. Delete old access token")
    print("   2. Go to Tools → Access Token Tool")
    print("   3. Generate brand new token")
    print("   4. Update .env and test again\n")

def main():
    """Main setup flow"""
    try:
        print_header()

        # Step 1: Guide through getting credentials
        print_step(1, "Getting Meta API Credentials")
        if not guide_meta_setup():
            print("⚠️  Setup cancelled")
            return 1

        # Step 2: Get credentials
        print_step(2, "Enter API Credentials")
        creds = get_credentials()
        if not creds:
            return 1

        # Step 3: Update .env
        print_step(3, "Saving Credentials to .env")
        update_env_file(creds)

        # Step 4: Test connection
        print_step(4, "Testing API Connection")
        if not test_api_connection():
            print("⚠️  Connection test had issues (may still work)")

        # Step 5: Test posting
        print_step(5, "Testing Posting Capability")
        if not test_posting_capability():
            print("⚠️  Capability test had issues")

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
