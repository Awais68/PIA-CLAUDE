#!/usr/bin/env python3
"""System Status Test - Check all integrations"""

import os
import sys
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

print("="*70)
print("🔍 ZOYA SYSTEM STATUS CHECK")
print("="*70)

# 1. Check .env variables
print("\n1️⃣  CREDENTIALS CHECK:")
print("-" * 70)

creds = {
    "LINKEDIN_ACCESS_TOKEN": "LinkedIn API Token",
    "LINKEDIN_PERSON_URN": "LinkedIn Person URN",
    "LINKEDIN_DRY_RUN": "LinkedIn Dry Run Mode",
    "TWITTER_API_KEY": "Twitter API Key",
    "TWITTER_BEARER_TOKEN": "Twitter Bearer Token",
    "WHATSAPP_ACCESS_TOKEN": "WhatsApp Token",
    "GOOGLE_CLIENT_ID": "Gmail Client ID",
    "ODOO_URL": "Odoo URL",
}

for key, desc in creds.items():
    val = os.getenv(key, "")
    if val:
        masked = val[:10] + "***" if len(val) > 10 else "***"
        print(f"✅ {desc:30} | {masked}")
    else:
        print(f"❌ {desc:30} | NOT SET")

# 2. Check directories
print("\n2️⃣  VAULT FOLDERS:")
print("-" * 70)

vault_path = Path("AI_Employee_Vault")
folders = ["Pending_Approval", "Approved", "Done", "Inbox", "Quarantine"]

for folder in folders:
    path = vault_path / folder
    if path.exists():
        files = len(list(path.glob("*")))
        print(f"✅ {folder:20} | {files} files")
    else:
        print(f"❌ {folder:20} | MISSING")

# 3. Test LinkedIn
print("\n3️⃣  LINKEDIN TEST:")
print("-" * 70)

try:
    from src.linkedin_poster import post_to_linkedin
    from src.config import LINKEDIN_DRY_RUN, LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN

    if not LINKEDIN_ACCESS_TOKEN:
        print("❌ LINKEDIN_ACCESS_TOKEN not set")
    elif not LINKEDIN_PERSON_URN:
        print("❌ LINKEDIN_PERSON_URN not set")
    else:
        test_content = "Test post from Zoya"
        result = post_to_linkedin(test_content)

        if result:
            print(f"✅ LinkedIn posting works (DRY_RUN={LINKEDIN_DRY_RUN})")
        else:
            print(f"⚠️  LinkedIn test failed - check token/URN")
except Exception as e:
    print(f"❌ LinkedIn error: {str(e)[:80]}")

# 4. Test Email
print("\n4️⃣  EMAIL TEST:")
print("-" * 70)

try:
    from src.mcp_servers.gmail_mcp import GmailMCPServer
    gmail = GmailMCPServer()
    if hasattr(gmail, 'authenticated') and gmail.authenticated:
        print("✅ Gmail authenticated")
    else:
        print("⚠️  Gmail not authenticated - needs OAuth")
except Exception as e:
    print(f"❌ Gmail error: {str(e)[:80]}")

# 5. Test Odoo
print("\n5️⃣  ODOO TEST:")
print("-" * 70)

try:
    from src.mcp_servers.odoo_mcp_real import OdooMCPServer
    odoo = OdooMCPServer()
    if hasattr(odoo, 'authenticated') and odoo.authenticated:
        print(f"✅ Odoo authenticated (UID: {odoo.uid})")
    else:
        print("⚠️  Odoo not connected - check URL/credentials")
except Exception as e:
    print(f"❌ Odoo error: {str(e)[:80]}")

# 6. Test Twitter
print("\n6️⃣  TWITTER TEST:")
print("-" * 70)

try:
    from src.mcp_servers.twitter_mcp_real import TwitterMCPServer
    from src.config import TWITTER_BEARER_TOKEN

    if TWITTER_BEARER_TOKEN:
        print("✅ Twitter credentials loaded")
    else:
        print("⚠️  TWITTER_BEARER_TOKEN not set")
except Exception as e:
    print(f"❌ Twitter error: {str(e)[:80]}")

# 7. Test WhatsApp
print("\n7️⃣  WHATSAPP TEST:")
print("-" * 70)

try:
    from src.config import WHATSAPP_ACCESS_TOKEN
    if WHATSAPP_ACCESS_TOKEN:
        print("✅ WhatsApp credentials loaded")
    else:
        print("⚠️  WHATSAPP_ACCESS_TOKEN not set")
except Exception as e:
    print(f"❌ WhatsApp error: {str(e)[:80]}")

# Summary
print("\n" + "="*70)
print("✅ TEST COMPLETE - Check results above")
print("="*70)
print("\n📋 SUMMARY:")
print("  • Set missing credentials in .env")
print("  • Run: python3 test_system_status.py")
print("  • For LinkedIn: Move post to Approved/, then run src/linkedin_poster.py\n")
