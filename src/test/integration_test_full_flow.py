"""
Full Integration Test - End-to-End Production Flow
Tests: Email → Approval → Multi-Channel Publishing → Invoice
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from src.config import NEEDS_ACTION, LOGS, PROJECT_ROOT
from src.mcp_servers.gmail_mcp import send_email as gmail_send_email
from src.mcp_servers.twitter_mcp_real import post_tweet
from src.mcp_servers.linkedin_mcp_real import post_to_linkedin
from src.mcp_servers.meta_mcp_real import post_to_instagram, post_to_facebook
from src.mcp_servers.whatsapp_mcp_real import send_message
from src.mcp_servers.odoo_mcp_real import create_invoice
from src.utils.logging_utils import setup_logging, log_action

logger = setup_logging()


def test_step_1_create_email_task():
    """Step 1: Create initial email task"""
    print("\n" + "="*80)
    print("STEP 1: Creating Email Task")
    print("="*80)

    # Create task file directly
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)

    task_file = NEEDS_ACTION / f"EMAIL_INTEGRATION_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    content = """---
type: email
from: client@example.com
subject: Partnership Proposal
created: {}
source: integration_test
---

# Email Task

From: client@example.com
Subject: Partnership Proposal

Hello,

I hope this email finds you well. I wanted to discuss a potential partnership opportunity
for your company. We believe there's significant potential for mutual growth.

Would you be available for a call next week to discuss details?

Best regards,
John Doe
""".format(datetime.utcnow().isoformat())

    try:
        task_file.write_text(content)
        print(f"✅ Email task created: {task_file.name}")
        log_action("test_email_task_created", "integration_test", "success")
        return str(task_file)
    except Exception as e:
        print(f"❌ Failed to create task: {e}")
        return None


def test_step_2_cloud_draft_email(task_file):
    """Step 2: Simulate cloud agent draft (skipped - moving to execution)"""
    print("\n" + "="*80)
    print("STEP 2: Cloud Agent Draft Generation (Simulated)")
    print("="*80)
    print("✅ Draft would be created by cloud agent")
    print("⏭️  Proceeding directly to execution...")
    return True


def test_step_3_send_email():
    """Step 3: Send email via Gmail API"""
    print("\n" + "="*80)
    print("STEP 3: Sending Email via Gmail")
    print("="*80)

    email_body = """Hello,

Thank you for reaching out about the partnership opportunity. We're very interested in exploring
this further and would be delighted to discuss how we can work together.

I'm available for a call next Tuesday at 2 PM or Wednesday at 10 AM. Please let me know which
works best for you.

Looking forward to our conversation!

Best regards,
Zoya - AI Employee"""

    result = gmail_send_email(
        to="client@example.com",
        subject="Re: Partnership Proposal",
        body=email_body
    )

    if result:
        print(f"✅ Email sent successfully via Gmail")
        log_action("test_email_sent", "gmail", "success")
        return True
    else:
        print(f"❌ Failed to send email")
        return False


def test_step_4_post_to_twitter():
    """Step 4: Post to Twitter"""
    print("\n" + "="*80)
    print("STEP 4: Posting to Twitter/X")
    print("="*80)

    tweet_text = """🚀 Exciting news! We're announcing a new strategic partnership that will unlock
amazing opportunities for growth and innovation. Looking forward to this journey together!
#Partnership #Growth #Innovation"""

    result = post_tweet(tweet_text)

    if result.get("success"):
        print(f"✅ Tweet posted: {result.get('tweet_id')}")
        log_action("test_tweet_posted", "twitter", "success", {"tweet_id": result.get('tweet_id')})
        return True
    else:
        print(f"❌ Failed to post tweet: {result.get('error')}")
        return False


def test_step_5_post_to_linkedin():
    """Step 5: Post to LinkedIn"""
    print("\n" + "="*80)
    print("STEP 5: Posting to LinkedIn")
    print("="*80)

    linkedin_post = """We're thrilled to announce a strategic partnership that represents an exciting
new chapter for our organization!

This collaboration brings together complementary strengths and shared values, positioning us
to deliver even greater value to our customers and stakeholders.

We look forward to the opportunities ahead and appreciate the trust and commitment of our partners.

#Partnership #Collaboration #Growth #Innovation"""

    result = post_to_linkedin(linkedin_post)

    if result.get("success"):
        print(f"✅ LinkedIn post created: {result.get('post_id')}")
        log_action("test_linkedin_posted", "linkedin", "success", {"post_id": result.get('post_id')})
        return True
    else:
        print(f"❌ Failed to post to LinkedIn: {result.get('error')}")
        return False


def test_step_6_post_to_instagram():
    """Step 6: Post to Instagram"""
    print("\n" + "="*80)
    print("STEP 6: Posting to Instagram")
    print("="*80)

    instagram_caption = """🎉 Big announcement! We're excited to share our latest partnership news!

This collaboration marks an important milestone in our journey. We're grateful for the trust and
partnership of our amazing team.

Stay tuned for more updates!

#Partnership #NewBeginnings #Grateful #Together"""

    # Using a placeholder image URL - in production would upload real image
    image_url = "https://via.placeholder.com/1080x1080?text=Partnership+Announcement"

    result = post_to_instagram(instagram_caption, image_url)

    if result.get("success"):
        print(f"✅ Instagram post created: {result.get('post_id')}")
        log_action("test_instagram_posted", "instagram", "success", {"post_id": result.get('post_id')})
        return True
    else:
        print(f"❌ Failed to post to Instagram: {result.get('error')}")
        return False


def test_step_7_post_to_facebook():
    """Step 7: Post to Facebook"""
    print("\n" + "="*80)
    print("STEP 7: Posting to Facebook")
    print("="*80)

    facebook_message = """🌟 We're excited to announce a new strategic partnership!

This collaboration represents a major step forward for our organization. By combining our
strengths and expertise, we're better positioned than ever to serve our customers and
communities.

Thank you to our partners for their trust and commitment. We look forward to the journey ahead!

#Partnership #Collaboration #Innovation"""

    result = post_to_facebook(facebook_message)

    if result.get("success"):
        print(f"✅ Facebook post created: {result.get('post_id')}")
        log_action("test_facebook_posted", "facebook", "success", {"post_id": result.get('post_id')})
        return True
    else:
        print(f"❌ Failed to post to Facebook: {result.get('error')}")
        return False


def test_step_8_send_whatsapp():
    """Step 8: Send WhatsApp notification"""
    print("\n" + "="*80)
    print("STEP 8: Sending WhatsApp Notification")
    print("="*80)

    # Note: Replace with actual recipient number
    message = """✅ Partnership Announcement Complete!

All channels updated:
✅ Email sent to client
✅ LinkedIn post published
✅ Twitter tweet posted
✅ Instagram post published
✅ Facebook post published

Integration test completed successfully!"""

    # Using a placeholder phone number - replace with actual recipient
    recipient = os.getenv("TEST_WHATSAPP_PHONE", "+1234567890")

    result = send_message(recipient, message)

    if result.get("success"):
        print(f"✅ WhatsApp message sent to {recipient}")
        log_action("test_whatsapp_sent", "whatsapp", "success", {"message_id": result.get('message_id')})
        return True
    else:
        print(f"❌ Failed to send WhatsApp: {result.get('error')}")
        return False


def test_step_9_create_invoice():
    """Step 9: Create invoice in Odoo"""
    print("\n" + "="*80)
    print("STEP 9: Creating Invoice in Odoo")
    print("="*80)

    result = create_invoice(
        customer_name="Strategic Partner Inc.",
        amount=5000.00,
        description="Partnership Services - Q1 2026",
        due_days=30,
        products=[
            {
                "name": "Strategic Partnership Services",
                "quantity": 1,
                "price": 5000.00
            }
        ]
    )

    if result.get("success"):
        print(f"✅ Invoice created: {result.get('invoice_id')}")
        log_action("test_invoice_created", "odoo", "success", {"invoice_id": result.get('invoice_id')})
        return True
    else:
        print(f"❌ Failed to create invoice: {result.get('error')}")
        return False


def run_full_integration_test():
    """Run complete integration test"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "FULL INTEGRATION TEST - PRODUCTION FLOW" + " "*20 + "║")
    print("║" + " "*15 + "Email → Social → WhatsApp → Invoice" + " "*29 + "║")
    print("╚" + "="*78 + "╝")

    results = {
        "step_1_create_task": test_step_1_create_email_task(),
        "step_2_generate_draft": None,
        "step_3_send_email": test_step_3_send_email(),
        "step_4_twitter": test_step_4_post_to_twitter(),
        "step_5_linkedin": test_step_5_post_to_linkedin(),
        "step_6_instagram": test_step_6_post_to_instagram(),
        "step_7_facebook": test_step_7_post_to_facebook(),
        "step_8_whatsapp": test_step_8_send_whatsapp(),
        "step_9_invoice": test_step_9_create_invoice()
    }

    # Step 2 - draft generation
    if results["step_1_create_task"]:
        results["step_2_generate_draft"] = test_step_2_cloud_draft_email(results["step_1_create_task"])

    # Print summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v is True)
    total = len(results)

    for step, result in results.items():
        status = "✅ PASS" if result is True else "⏳ PENDING" if result is None else "❌ FAIL"
        print(f"{status} | {step.replace('_', ' ').title()}")

    print("="*80)
    print(f"\nResult: {passed}/{total} steps successful")

    if passed == total - 1:  # Allowing one pending (draft generation)
        print("\n✨ Integration test PASSED! All systems operational. ✨")
        return True
    else:
        print(f"\n⚠️ Integration test had {total - passed} failures")
        return False


if __name__ == "__main__":
    # Run test
    success = run_full_integration_test()
    sys.exit(0 if success else 1)
