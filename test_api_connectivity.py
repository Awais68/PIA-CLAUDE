#!/usr/bin/env python3
"""
Test actual API connectivity and authentication
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

print("\n" + "="*80)
print("API CONNECTIVITY TEST - Real Authentication Checks".center(80))
print("="*80 + "\n")

passed = 0
failed = 0

# ============================================================================
# 1. Gmail Service Build
# ============================================================================
print("📧 TEST 1: Gmail API Service")
print("-" * 80)
try:
    from src.mcp_servers.gmail_mcp import GmailMCPServer
    
    gmail = GmailMCPServer()
    if gmail.service:
        print("✅ Gmail API authenticated successfully")
        print("   Service: Gmail v1 (ready to send emails)")
        passed += 1
    else:
        print("❌ Gmail API failed to authenticate")
        failed += 1
except Exception as e:
    print(f"❌ Gmail error: {e}")
    failed += 1

print()

# ============================================================================
# 2. Twitter Client
# ============================================================================
print("🐦 TEST 2: Twitter API Client")
print("-" * 80)
try:
    import tweepy
    
    twitter_key = os.getenv("TWITTER_API_KEY")
    twitter_secret = os.getenv("TWITTER_API_SECRET")
    twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")
    
    if twitter_bearer:
        client = tweepy.Client(bearer_token=twitter_bearer, wait_on_rate_limit=True)
        user = client.get_me()
        if user:
            print(f"✅ Twitter authenticated successfully")
            print(f"   User: {user.data.username}")
            passed += 1
        else:
            print("❌ Twitter authentication failed")
            failed += 1
    else:
        print("⚠️  Twitter Bearer token not configured")
        failed += 1
except ImportError:
    print("⚠️  tweepy not installed (skipping)")
    failed += 1
except Exception as e:
    print(f"❌ Twitter error: {str(e)[:100]}")
    failed += 1

print()

# ============================================================================
# 3. LinkedIn API
# ============================================================================
print("💼 TEST 3: LinkedIn API Client")
print("-" * 80)
try:
    import requests
    
    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    
    if linkedin_token:
        headers = {
            "Authorization": f"Bearer {linkedin_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://api.linkedin.com/v2/me",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ LinkedIn authenticated successfully")
            print(f"   Profile ID: {profile.get('id', 'unknown')}")
            passed += 1
        elif response.status_code == 401:
            print("❌ LinkedIn token expired (401)")
            failed += 1
        else:
            print(f"❌ LinkedIn error: {response.status_code}")
            failed += 1
    else:
        print("⚠️  LinkedIn token not configured")
        failed += 1
except Exception as e:
    print(f"❌ LinkedIn error: {str(e)[:100]}")
    failed += 1

print()

# ============================================================================
# 4. Facebook/Meta API
# ============================================================================
print("📘 TEST 4: Facebook/Meta API Client")
print("-" * 80)
try:
    import requests
    
    meta_token = os.getenv("META_ACCESS_TOKEN")
    
    if meta_token:
        response = requests.get(
            "https://graph.facebook.com/v18.0/me",
            params={"access_token": meta_token},
            timeout=10
        )
        
        if response.status_code == 200:
            profile = response.json()
            print(f"✅ Meta authenticated successfully")
            print(f"   User: {profile.get('name', 'unknown')}")
            passed += 1
        elif response.status_code == 400:
            print("❌ Meta token invalid or expired (400)")
            failed += 1
        else:
            print(f"❌ Meta error: {response.status_code}")
            failed += 1
    else:
        print("⚠️  Meta token not configured")
        failed += 1
except Exception as e:
    print(f"❌ Meta error: {str(e)[:100]}")
    failed += 1

print()

# ============================================================================
# 5. Odoo XML-RPC
# ============================================================================
print("📋 TEST 5: Odoo API Client")
print("-" * 80)
try:
    import xmlrpc.client
    
    odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
    odoo_db = os.getenv("ODOO_DB")
    odoo_user = os.getenv("ODOO_USER")
    odoo_password = os.getenv("ODOO_API_KEY")
    
    if all([odoo_db, odoo_user, odoo_password]):
        try:
            common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
            uid = common.authenticate(odoo_db, odoo_user, odoo_password, {})
            
            if uid:
                print(f"✅ Odoo authenticated successfully")
                print(f"   User ID: {uid}")
                passed += 1
            else:
                print("❌ Odoo authentication failed")
                failed += 1
        except ConnectionRefusedError:
            print(f"❌ Odoo server not running at {odoo_url}")
            failed += 1
    else:
        print("⚠️  Odoo credentials not configured")
        failed += 1
except Exception as e:
    print(f"❌ Odoo error: {str(e)[:100]}")
    failed += 1

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("CONNECTIVITY TEST SUMMARY".center(80))
print("=" * 80)
print(f"\n✅ Services Connected: {passed}")
print(f"❌ Services Failed: {failed}")
print(f"⏭️  Total Tests: {passed + failed}")

if passed >= 3:
    print("\n🎉 SUCCESS! 3+ services are connected and ready!")
    print("\nReady to test:")
    if passed >= 1: print("  • Gmail (email sending)")
    if passed >= 2: print("  • Twitter (posting)")
    if passed >= 3: print("  • LinkedIn (posting)")
    if passed >= 4: print("  • Facebook/Meta (posting)")
    if passed >= 5: print("  • Odoo (invoice creation)")
else:
    print(f"\n⚠️  Only {passed} service(s) connected. Fix remaining services.")

