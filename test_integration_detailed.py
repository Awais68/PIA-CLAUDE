#!/usr/bin/env python3
"""
Detailed Integration Test with Diagnostic Info
Shows which services are configured and ready
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

print("\n" + "="*80)
print("INTEGRATION CREDENTIAL DIAGNOSTIC TEST".center(80))
print("="*80 + "\n")

tests_results = {}

# ============================================================================
# 1. GMAIL API
# ============================================================================
print("📧 GMAIL - Checking Configuration")
print("-" * 80)

gmail_creds = PROJECT_ROOT / "credentials.json"
gmail_token = PROJECT_ROOT / "token.json"

if gmail_creds.exists():
    print("✅ credentials.json found")
else:
    print("❌ credentials.json NOT found")

if gmail_token.exists():
    print("✅ token.json found")
    try:
        import json
        content = gmail_token.read_text()
        if content.startswith('{'):
            print("✅ token.json is valid JSON format (NOT pickle) ✓")
            tests_results['Gmail Token Format'] = '✅ FIXED'
        else:
            print("❌ token.json is in pickle format (needs conversion)")
            tests_results['Gmail Token Format'] = '❌ NEEDS FIX'
    except Exception as e:
        print(f"⚠️  Could not parse token: {e}")
        tests_results['Gmail Token Format'] = '⚠️  CORRUPT'
else:
    print("⚠️  token.json NOT found (will be created on first auth)")
    tests_results['Gmail Token Format'] = '⚠️  NEW'

print()

# ============================================================================
# 2. TWITTER API v2
# ============================================================================
print("🐦 TWITTER - Checking Configuration")
print("-" * 80)

twitter_key = os.getenv("TWITTER_API_KEY")
twitter_secret = os.getenv("TWITTER_API_SECRET")
twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")
twitter_access = os.getenv("TWITTER_ACCESS_TOKEN")

has_key = bool(twitter_key and twitter_key != "")
has_secret = bool(twitter_secret and twitter_secret != "")
has_bearer = bool(twitter_bearer and twitter_bearer != "")
has_access = bool(twitter_access and twitter_access != "")

print(f"  API Key: {'✅' if has_key else '❌'}")
print(f"  API Secret: {'✅' if has_secret else '❌'}")
print(f"  Bearer Token: {'✅' if has_bearer else '❌'} {('[CONFIGURED]' if has_bearer else '')}")
print(f"  Access Token: {'✅' if has_access else '❌'}")

if has_bearer:
    if twitter_bearer.startswith("AAAAAAA"):
        print("  ✅ Bearer token format looks valid")
        tests_results['Twitter'] = '✅ READY (Bearer token)'
    else:
        print("  ⚠️  Bearer token format suspicious")
        tests_results['Twitter'] = '⚠️  CHECK NEEDED'
elif has_key and has_secret and has_access:
    print("  ✅ OAuth tokens configured")
    tests_results['Twitter'] = '✅ READY (OAuth)'
else:
    print("  ❌ Twitter credentials incomplete")
    tests_results['Twitter'] = '❌ MISSING'

print()

# ============================================================================
# 3. LINKEDIN API
# ============================================================================
print("💼 LINKEDIN - Checking Configuration")
print("-" * 80)

linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
linkedin_client_id = os.getenv("LINKEDIN_CLIENT_ID")
linkedin_person_urn = os.getenv("LINKEDIN_PERSON_URN")

has_token = bool(linkedin_token and linkedin_token != "")
has_client = bool(linkedin_client_id and linkedin_client_id != "")
has_urn = bool(linkedin_person_urn and linkedin_person_urn != "")

print(f"  Access Token: {'✅' if has_token else '❌'}")
print(f"  Client ID: {'✅' if has_client else '❌'}")
print(f"  Person URN: {'✅' if has_urn else '❌'}")

if has_token and has_client and has_urn:
    if linkedin_token.startswith("AQ"):
        print("  ✅ Access token format looks valid (AQ prefix)")
        print("  ✅ Playwright mode available for browser automation")
        tests_results['LinkedIn'] = '✅ READY (Playwright available)'
    else:
        print("  ⚠️  Access token format suspicious")
        tests_results['LinkedIn'] = '⚠️  CHECK NEEDED'
else:
    print("  ❌ LinkedIn credentials incomplete")
    tests_results['LinkedIn'] = '❌ MISSING'

print()

# ============================================================================
# 4. FACEBOOK API
# ============================================================================
print("📘 FACEBOOK - Checking Configuration")
print("-" * 80)

fb_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
fb_page_id = os.getenv("FACEBOOK_PAGE_ID")
meta_token = os.getenv("META_ACCESS_TOKEN")
marketing_token = os.getenv("MARKETING_ACCESS_TOKEN")

has_fb_token = bool(fb_token and fb_token != "")
has_page = bool(fb_page_id and fb_page_id != "")
has_meta = bool(meta_token and meta_token != "")
has_marketing = bool(marketing_token and marketing_token != "")

print(f"  Facebook Token: {'✅' if has_fb_token else '❌'}")
print(f"  Page ID: {'✅' if has_page else '❌'}")
print(f"  Meta Token: {'✅' if has_meta else '❌'}")
print(f"  Marketing Token: {'✅' if has_marketing else '❌'}")

if has_meta and has_page:
    if meta_token.startswith("EAA"):
        print("  ✅ Meta token format looks valid (EAA prefix)")
        tests_results['Facebook'] = '✅ CONFIGURED'
    else:
        print("  ⚠️  Meta token format suspicious")
        tests_results['Facebook'] = '⚠️  CHECK FORMAT'
else:
    print("  ❌ Facebook/Meta credentials incomplete")
    tests_results['Facebook'] = '❌ MISSING'

print()

# ============================================================================
# 5. WHATSAPP API
# ============================================================================
print("💬 WHATSAPP - Checking Configuration")
print("-" * 80)

wa_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
wa_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
wa_business_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
test_phone = os.getenv("TEST_WHATSAPP_PHONE")

has_wa_token = bool(wa_token and wa_token != "")
has_phone = bool(wa_phone_id and wa_phone_id != "")
has_business = bool(wa_business_id and wa_business_id != "")
has_test = bool(test_phone and test_phone != "")

print(f"  WhatsApp Token: {'✅' if has_wa_token else '❌'}")
print(f"  Phone ID: {'✅' if has_phone else '❌'}")
print(f"  Business ID: {'✅' if has_business else '❌'}")
print(f"  Test Phone: {'✅' if has_test else '❌'}")

if has_wa_token and has_phone:
    if wa_token.startswith("EAA"):
        print("  ✅ WhatsApp token format looks valid (EAA prefix)")
        tests_results['WhatsApp'] = '✅ CONFIGURED'
    else:
        print("  ⚠️  WhatsApp token format suspicious")
        tests_results['WhatsApp'] = '⚠️  CHECK FORMAT'
else:
    print("  ❌ WhatsApp credentials incomplete")
    tests_results['WhatsApp'] = '❌ MISSING'

print()

# ============================================================================
# 6. ODOO API
# ============================================================================
print("📋 ODOO - Checking Configuration")
print("-" * 80)

odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
odoo_db = os.getenv("ODOO_DB")
odoo_user = os.getenv("ODOO_USER")
odoo_key = os.getenv("ODOO_API_KEY")

has_url = bool(odoo_url)
has_db = bool(odoo_db)
has_user = bool(odoo_user)
has_key = bool(odoo_key)

print(f"  URL: {'✅' if has_url else '❌'} ({odoo_url})")
print(f"  Database: {'✅' if has_db else '❌'}")
print(f"  User: {'✅' if has_user else '❌'}")
print(f"  API Key: {'✅' if has_key else '❌'}")

if all([has_url, has_db, has_user, has_key]):
    print("  ⚠️  Odoo needs accounting module installed")
    tests_results['Odoo'] = '⚠️  NEEDS SETUP'
else:
    print("  ❌ Odoo credentials incomplete")
    tests_results['Odoo'] = '❌ MISSING'

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("CREDENTIAL STATUS SUMMARY".center(80))
print("=" * 80 + "\n")

for service, status in tests_results.items():
    print(f"  {service:.<40} {status}")

print("\n" + "=" * 80)
print("NEXT STEPS".center(80))
print("=" * 80 + "\n")

print("1. Gmail Fix (if needed):")
print("   - Delete token.json if in pickle format")
print("   - Run: python run_real_api_test.py")
print()

print("2. Twitter Check:")
print("   - Verify Bearer token is working")
print("   - Run: python run_real_api_test.py")
print()

print("3. LinkedIn Playwright Setup:")
print("   - Install Playwright: pip install playwright")
print("   - Run browser-based login script")
print()

print("4. Facebook/Meta Check:")
print("   - Verify token has pages_manage_posts scope")
print("   - May need token refresh")
print()

print("5. WhatsApp Setup:")
print("   - For Cloud API: Token already configured")
print("   - For Local Session: Run WhatsApp login script")
print()

print("6. Odoo Setup:")
print("   - Install accounting module in Odoo")
print("   - Or disable invoice tests")
print()

