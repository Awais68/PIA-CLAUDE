#!/usr/bin/env python3
"""
Quick Credential Status Checker
Shows which credentials need immediate attention
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def check_env_var(name: str, required: bool = True) -> bool:
    """Check if environment variable is set and not empty"""
    value = os.getenv(name, '').strip()
    return bool(value) if required else True


def get_token_age(token: str) -> str:
    """Estimate token type and age hints"""
    if token.startswith('AAA'):
        return "Twitter (v2)"
    elif token.startswith('AQ'):
        return "LinkedIn (OAuth)"
    elif token.startswith('EAA'):
        return "Meta (Facebook/WhatsApp)"
    elif token.startswith('urn:li:'):
        return "LinkedIn URN"
    else:
        return "Unknown type"


def print_status_table():
    """Print credential status table"""
    print("\n" + "="*90)
    print("🔐 CREDENTIAL STATUS QUICK CHECK")
    print("="*90 + "\n")

    # Twitter
    print("🐦 TWITTER/X")
    print("-" * 90)
    twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN', '')
    twitter_key = os.getenv('TWITTER_API_KEY', '')
    twitter_secret = os.getenv('TWITTER_API_SECRET', '')

    print(f"  Bearer Token:  {'✅ SET' if twitter_bearer else '❌ MISSING'} ({len(twitter_bearer)} chars)")
    print(f"  API Key:       {'✅ SET' if twitter_key else '❌ MISSING'} ({len(twitter_key)} chars)")
    print(f"  API Secret:    {'✅ SET' if twitter_secret else '❌ MISSING'} ({len(twitter_secret)} chars)")

    if twitter_bearer and twitter_bearer.startswith('AAAA'):
        print(f"  ✅ Token format looks correct (starts with AAAA)")
    elif twitter_bearer:
        print(f"  ⚠️  Token format unusual (should start with AAAA)")

    # Facebook
    print("\n📘 FACEBOOK/META")
    print("-" * 90)
    fb_token = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
    meta_token = os.getenv('META_ACCESS_TOKEN', '')
    marketing_token = os.getenv('MARKETING_ACCESS_TOKEN', '')
    fb_page = os.getenv('FACEBOOK_PAGE_ID', '')

    print(f"  Facebook Token:  {'✅ SET' if fb_token else '❌ MISSING'} ({len(fb_token)} chars)")
    print(f"  Meta Token:      {'✅ SET' if meta_token else '❌ MISSING'} ({len(meta_token)} chars)")
    print(f"  Marketing Token: {'✅ SET' if marketing_token else '❌ MISSING'} ({len(marketing_token)} chars)")
    print(f"  Page ID:         {'✅ SET' if fb_page else '❌ MISSING'} ({fb_page})")

    if fb_token and not fb_token.startswith('EAA'):
        print(f"  ⚠️  Facebook token format unusual (should start with EAA)")
    if meta_token and not meta_token.startswith('EAA'):
        print(f"  ⚠️  Meta token format unusual (should start with EAA)")

    # WhatsApp
    print("\n💬 WHATSAPP BUSINESS")
    print("-" * 90)
    wa_token = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
    wa_business_token = os.getenv('WHATSAPP_BUSINESS_TOKEN', '')
    wa_phone_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
    wa_account_id = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID', '')

    print(f"  Access Token:    {'✅ SET' if wa_token else '❌ MISSING'} ({len(wa_token)} chars)")
    print(f"  Business Token:  {'✅ SET' if wa_business_token else '❌ MISSING'} ({len(wa_business_token)} chars)")
    print(f"  Phone ID:        {'✅ SET' if wa_phone_id else '❌ MISSING'} ({wa_phone_id})")
    print(f"  Account ID:      {'✅ SET' if wa_account_id else '❌ MISSING'} ({wa_account_id})")

    if wa_phone_id and wa_phone_id.startswith('+'):
        print(f"  ⚠️  Phone ID format unusual (should be numeric, not E.164)")

    # LinkedIn
    print("\n💼 LINKEDIN")
    print("-" * 90)
    li_client_id = os.getenv('LINKEDIN_CLIENT_ID', '')
    li_secret = os.getenv('LINKEDIN_CLIENT_SECRET', '')
    li_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
    li_urn = os.getenv('LINKEDIN_PERSON_URN', '')
    li_email = os.getenv('LINKEDIN_EMAIL', '')
    li_password = os.getenv('LINKEDIN_PASSWORD', '')

    print(f"  Client ID:       {'✅ SET' if li_client_id else '❌ MISSING'} ({li_client_id})")
    print(f"  Client Secret:   {'✅ SET' if li_secret else '❌ MISSING'} ({len(li_secret)} chars)")
    print(f"  Access Token:    {'✅ SET' if li_token else '❌ MISSING'} ({len(li_token)} chars)")
    print(f"  Person URN:      {'✅ SET' if li_urn else '❌ MISSING'} ({li_urn})")
    print(f"  Email (for auth):    {'✅ SET' if li_email else '⚠️  MISSING'}")
    print(f"  Password (for auth): {'✅ SET' if li_password else '⚠️  MISSING'}")

    if li_token and not li_token.startswith('AQ'):
        print(f"  ⚠️  Token format unusual (should start with AQ)")
    if li_urn and not li_urn.startswith('urn:li:person:'):
        print(f"  ⚠️  Person URN format incorrect")

    # Summary
    print("\n" + "="*90)
    print("📊 SUMMARY")
    print("="*90)

    issues = []

    # Twitter
    if not twitter_bearer:
        issues.append("🐦 Twitter: Missing bearer token")
    elif not twitter_bearer.startswith('AAAA'):
        issues.append("🐦 Twitter: Bearer token format unusual")

    # Facebook
    if not fb_token and not meta_token:
        issues.append("📘 Facebook: Both tokens missing")
    elif not fb_token or not meta_token:
        issues.append("📘 Facebook: One token missing (regenerate both)")

    # WhatsApp
    if not wa_token or not wa_business_token:
        issues.append("💬 WhatsApp: One or both tokens missing")
    if wa_phone_id.startswith('+'):
        issues.append("💬 WhatsApp: Phone ID should be numeric (verify at business.facebook.com)")

    # LinkedIn
    if not li_token:
        issues.append("💼 LinkedIn: Missing access token")
    elif not li_token.startswith('AQ'):
        issues.append("💼 LinkedIn: Token format unusual")

    if not li_urn:
        issues.append("💼 LinkedIn: Missing person URN")
    elif not li_urn.startswith('urn:li:person:'):
        issues.append("💼 LinkedIn: Person URN format incorrect")

    if not li_email or not li_password:
        issues.append("💼 LinkedIn: Email/password missing (needed for Playwright auth)")

    if issues:
        print("\n🔴 ISSUES DETECTED:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✅ All credentials appear to be configured!")

    print("\n" + "="*90)
    print("🚀 NEXT STEPS:")
    print("="*90)

    if issues:
        print("\n1. Read CREDENTIALS_ACTION_PLAN.md for detailed instructions")
        print("2. Fix issues in priority order (Facebook → WhatsApp → LinkedIn → Twitter)")
        print("3. Run full validation:")
        print("   python check_credentials.py")
    else:
        print("\n1. Run full validation to test connectivity:")
        print("   python check_credentials.py")
        print("2. Fix any API errors returned")

    print("\n" + "="*90 + "\n")


def show_help():
    """Show help information"""
    print("""
📖 CREDENTIAL VALIDATION TOOLS

Available commands:
  python quick_credential_status.py    - Show this quick status check
  python check_credentials.py           - Full validation with API tests
  python linkedin_playwright_login.py   - Browser-based LinkedIn auth
  python linkedin_playwright_validator.py - Validate LinkedIn with browser

Documentation:
  CREDENTIAL_VALIDATION_GUIDE.md       - Complete reference
  CREDENTIALS_ACTION_PLAN.md           - Step-by-step fix instructions
  CREDENTIAL_SETUP_SUMMARY.md          - Overview and timeline

For more help, read the documentation files above.
""")


if __name__ == '__main__':
    import sys

    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()
    else:
        print_status_table()
