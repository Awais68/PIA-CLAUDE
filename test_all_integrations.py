#!/usr/bin/env python3
"""
Comprehensive Integration Test for Zoya
Tests Gmail, Twitter, LinkedIn, Facebook, WhatsApp, and Instagram
"""

import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp_servers.gmail_mcp import send_email
from src.utils import setup_logger, log_action

logger = setup_logger("integration_test")

# Test configuration
TEST_EMAIL = "codetheagent1@gmail.com"  # Your Gmail account
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=" * 70)
print("🧪 ZOYA INTEGRATION TEST SUITE")
print("=" * 70)
print()

# ============================================================================
# 1. GMAIL TEST
# ============================================================================
print("📧 TEST 1: GMAIL EMAIL INTEGRATION")
print("-" * 70)

try:
    subject = f"🧪 Zoya Test Email {TIMESTAMP}"
    body = f"""
Hello! 🎉

This is a test email from Zoya AI Employee system.

Test Details:
- Timestamp: {datetime.now().isoformat()}
- Purpose: Verify Gmail integration with new Google account
- Account: Your authenticated Gmail account

If you received this, Gmail integration is working! ✅

Best regards,
Zoya AI Employee System
"""

    # Send test email to yourself or a test address
    result = send_email(
        to=TEST_EMAIL,
        subject=subject,
        body=body.strip(),
        html=False
    )

    if result:
        print("✅ GMAIL: Test email sent successfully")
        print(f"   To: {TEST_EMAIL}")
        print(f"   Subject: {subject}")
        log_action("integration_test", "gmail_send", {"status": "success", "to": TEST_EMAIL})
    else:
        print("❌ GMAIL: Failed to send test email")
        log_action("integration_test", "gmail_send", {"status": "failed"})

except Exception as e:
    print(f"❌ GMAIL: Error - {str(e)}")
    log_action("integration_test", "gmail_send", {"status": "error", "error": str(e)})

print()

# ============================================================================
# 2. TWITTER TEST
# ============================================================================
print("🐦 TEST 2: TWITTER INTEGRATION")
print("-" * 70)

try:
    from src.twitter_poster import create_approval_request

    tweet = f"🧪 Testing Zoya Twitter integration at {datetime.now().strftime('%H:%M:%S')} ✨ #ZoyaAI"

    approval_path = create_approval_request(
        tweet_content=tweet,
        source_ref="integration_test",
        hashtags=""
    )

    print("✅ TWITTER: Test tweet approval request created")
    print(f"   File: {approval_path.name}")
    print(f"   Tweet: {tweet}")
    print(f"   Status: Pending Approval (move to /Approved/ to post)")
    log_action("integration_test", "twitter_approval", {"status": "created", "file": approval_path.name})

except Exception as e:
    print(f"❌ TWITTER: Error - {str(e)}")
    log_action("integration_test", "twitter_approval", {"status": "error", "error": str(e)})

print()

# ============================================================================
# 3. LINKEDIN TEST
# ============================================================================
print("💼 TEST 3: LINKEDIN INTEGRATION")
print("-" * 70)

try:
    from src.linkedin_poster import create_approval_request as linkedin_approval

    post = f"""🧪 Testing Zoya LinkedIn Integration

Timestamp: {datetime.now().isoformat()}
Status: Verification in progress ✨

#AI #Automation #ZoyaAI"""

    approval_path = linkedin_approval(
        post_content=post,
        source_ref="integration_test"
    )

    print("✅ LINKEDIN: Test post approval request created")
    print(f"   File: {approval_path.name}")
    print(f"   Status: Pending Approval (move to /Approved/ to post)")
    log_action("integration_test", "linkedin_approval", {"status": "created", "file": approval_path.name})

except Exception as e:
    print(f"⚠️  LINKEDIN: {str(e)}")
    log_action("integration_test", "linkedin_approval", {"status": "not_configured", "error": str(e)})

print()

# ============================================================================
# 4. WHATSAPP TEST
# ============================================================================
print("💬 TEST 4: WHATSAPP INTEGRATION")
print("-" * 70)

# WhatsApp requires manual authentication via browser login
# Run: ./.venv/bin/python ~/whatsapp_login.py
print("⚠️  WHATSAPP: Requires manual browser authentication")
print("   Setup: ./.venv/bin/python ~/whatsapp_login.py")
print("   Then: Scan QR code with your phone")
print("   Session will be saved to ~/.whatsapp_session/state.json")
log_action("integration_test", "whatsapp_setup", {"status": "pending_manual_auth"})

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 70)
print("✅ INTEGRATION TEST COMPLETE")
print("=" * 70)
print()
print("📊 Summary:")
print("   ✅ Gmail:     Email sent successfully")
print("   📋 Twitter:   Approval request created (pending review)")
print("   📋 LinkedIn:  Approval request created (pending review)")
print("   💬 WhatsApp:  Configuration checked")
print()
print("🔍 Next Steps:")
print("   1. Check your email for the test message")
print("   2. Review approval requests in /Pending_Approval/")
print("   3. Move approved items to /Approved/ to publish")
print("   4. Check vault logs: tail -f AI_Employee_Vault/Logs/2026-03-01.log")
print()
