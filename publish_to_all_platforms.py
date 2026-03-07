#!/usr/bin/env python3
"""
🚀 PUBLISH TO ALL PLATFORMS
Posts content to Twitter, LinkedIn, Facebook, and WhatsApp
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.config import APPROVED, DONE
from src.utils import setup_logger, log_action

logger = setup_logger("publish_all_platforms")

# ============================================================================
# HELPER: Extract content from markdown files
# ============================================================================
def extract_content(file_path):
    """Extract content from markdown file, skipping YAML frontmatter."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Skip YAML frontmatter (between ---)
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2].strip()

    # Remove markdown headers and get just the text
    lines = content.split('\n')
    text_lines = []
    for line in lines:
        # Skip header lines
        if not line.startswith('#'):
            text_lines.append(line)

    return '\n'.join(text_lines).strip()


# ============================================================================
# 1. TWITTER
# ============================================================================
def publish_to_twitter():
    """Post to Twitter using tweepy"""
    print("\n" + "="*90)
    print("🐦 PUBLISHING TO TWITTER")
    print("="*90)

    try:
        twitter_file = Path("AI_Employee_Vault/Approved/general/TWITTER_20260301_105746.md")

        if not twitter_file.exists():
            print("⚠️  Twitter file not found")
            return False

        # Extract tweet content
        content = extract_content(twitter_file)

        # Get just the tweet text (between ## Draft Tweet and ## Hashtags)
        tweet_match = re.search(r'## Draft Tweet\n(.*?)\n##', content, re.DOTALL)
        if tweet_match:
            tweet_text = tweet_match.group(1).strip()
        else:
            tweet_text = content[:280]

        print(f"\n📝 Tweet Content:\n{tweet_text}\n")

        # Try to post using tweepy
        try:
            import tweepy

            # Get credentials
            api_key = os.getenv("TWITTER_API_KEY")
            api_secret = os.getenv("TWITTER_API_SECRET")
            access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

            if not all([api_key, api_secret, access_token, access_token_secret]):
                print("⚠️  Missing Twitter credentials")
                print(f"   API_KEY: {'✓' if api_key else '✗'}")
                print(f"   API_SECRET: {'✓' if api_secret else '✗'}")
                print(f"   ACCESS_TOKEN: {'✓' if access_token else '✗'}")
                print(f"   ACCESS_TOKEN_SECRET: {'✓' if access_token_secret else '✗'}")
                return False

            # Initialize client with OAuth 1.0a
            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)

            # Post tweet
            result = api.update_status(status=tweet_text)

            print(f"✅ TWITTER POST PUBLISHED")
            print(f"   Tweet ID: {result.id}")
            print(f"   Status: Successfully posted")
            print(f"   URL: https://twitter.com/i/web/status/{result.id}")

            log_action("publish_all", "twitter", {"tweet_id": result.id, "status": "published"}, "success")
            return True

        except ImportError:
            print("⚠️  tweepy not installed. Run: uv add tweepy")
            return False
        except Exception as e:
            print(f"❌ Twitter API Error: {str(e)}")
            log_action("publish_all", "twitter", {"error": str(e)}, "error")
            return False

    except Exception as e:
        print(f"❌ Twitter Error: {str(e)}")
        return False


# ============================================================================
# 2. LINKEDIN
# ============================================================================
def publish_to_linkedin():
    """Post to LinkedIn using their API"""
    print("\n" + "="*90)
    print("💼 PUBLISHING TO LINKEDIN")
    print("="*90)

    try:
        linkedin_file = Path("AI_Employee_Vault/Approved/general/LINKEDIN_20260301_105746.md")

        if not linkedin_file.exists():
            print("⚠️  LinkedIn file not found")
            return False

        # Extract post content
        content = extract_content(linkedin_file)

        # Get just the post text
        post_match = re.search(r'## Draft Post\n(.*?)\n##', content, re.DOTALL)
        if post_match:
            post_text = post_match.group(1).strip()
        else:
            post_text = content

        print(f"\n📝 LinkedIn Post:\n{post_text[:300]}...\n")

        try:
            import requests

            # Get credentials
            access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
            person_urn = os.getenv("LINKEDIN_PERSON_URN")

            if not access_token or not person_urn:
                print("⚠️  Missing LinkedIn credentials")
                print(f"   ACCESS_TOKEN: {'✓' if access_token else '✗'}")
                print(f"   PERSON_URN: {'✓' if person_urn else '✗'}")
                return False

            # LinkedIn API v2 endpoint
            url = "https://api.linkedin.com/v2/ugcPosts"

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "author": person_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": post_text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }

            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 201 and "id" in response_data:
                post_id = response_data["id"]
                print(f"✅ LINKEDIN POST PUBLISHED")
                print(f"   Post ID: {post_id}")
                print(f"   Status: Successfully posted")
                log_action("publish_all", "linkedin", {"post_id": post_id, "status": "published"}, "success")
                return True
            else:
                error_msg = response_data.get("message", "Unknown error")
                print(f"❌ LinkedIn API Error: {error_msg}")
                print(f"   Response: {response_data}")
                log_action("publish_all", "linkedin", {"error": error_msg, "status": "failed"}, "error")
                return False

        except ImportError:
            print("⚠️  requests not installed. Run: uv add requests")
            return False
        except Exception as e:
            print(f"❌ LinkedIn API Error: {str(e)}")
            log_action("publish_all", "linkedin", {"error": str(e)}, "error")
            return False

    except Exception as e:
        print(f"❌ LinkedIn Error: {str(e)}")
        return False


# ============================================================================
# 3. FACEBOOK
# ============================================================================
def publish_to_facebook():
    """Post to Facebook using Graph API"""
    print("\n" + "="*90)
    print("📱 PUBLISHING TO FACEBOOK")
    print("="*90)

    try:
        import requests

        # Get credentials
        access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
        page_id = os.getenv("FACEBOOK_PAGE_ID")

        if not access_token or not page_id:
            print("⚠️  Missing Facebook credentials")
            print(f"   ACCESS_TOKEN: {'✓' if access_token else '✗'}")
            print(f"   PAGE_ID: {'✓' if page_id else '✗'}")
            return False

        # Facebook announcement message
        message = """🚀 Announcing the Launch of Digital Employee System

I'm thrilled to share that the Digital Employee System is now officially LIVE!

As the Founder, I'm proud to present a breakthrough in AI-powered automation that transforms how businesses operate.

✨ What's Live:

🤖 Intelligent Automation
📧 Email Integration (Gmail API)
📱 Social Media Management (Twitter, LinkedIn, Facebook)
💬 WhatsApp Messaging
📊 Real-time Dashboard
✅ Health Monitoring & Alerts

🎯 Key Features:
• AI-Powered Task Automation
• Multi-Channel Integration
• Human-in-the-Loop Approvals
• Real-time Monitoring
• Complete Audit Logging

🚀 The Future of Business Automation is HERE!

Thank you for being part of this journey!

#DigitalEmployee #AI #Automation #FutureOfWork #BusinessTech #Innovation #Founder"""

        print(f"\n📝 Facebook Post:\n{message[:300]}...\n")

        # Post to Facebook
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        params = {
            "message": message,
            "access_token": access_token
        }

        response = requests.post(url, data=params)
        response_data = response.json()

        if response.status_code == 200 and "id" in response_data:
            post_id = response_data["id"]
            print(f"✅ FACEBOOK POST PUBLISHED")
            print(f"   Post ID: {post_id}")
            print(f"   Status: Successfully posted")
            log_action("publish_all", "facebook", {"post_id": post_id, "status": "published"}, "success")
            return True
        else:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            print(f"❌ Facebook API Error: {error_msg}")
            print(f"   Response: {response_data}")
            log_action("publish_all", "facebook", {"error": error_msg, "status": "failed"}, "error")
            return False

    except ImportError:
        print("⚠️  requests not installed. Run: uv add requests")
        return False
    except Exception as e:
        print(f"❌ Facebook Error: {str(e)}")
        log_action("publish_all", "facebook", {"error": str(e)}, "error")
        return False


# ============================================================================
# 4. WHATSAPP
# ============================================================================
def send_whatsapp_message():
    """Send WhatsApp message"""
    print("\n" + "="*90)
    print("💬 SENDING WHATSAPP MESSAGE")
    print("="*90)

    try:
        import requests

        # Get credentials
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        recipient = os.getenv("OWNER_WHATSAPP_NUMBER")

        if not all([access_token, phone_number_id, recipient]):
            print("⚠️  Missing WhatsApp credentials")
            print(f"   ACCESS_TOKEN: {'✓' if access_token else '✗'}")
            print(f"   PHONE_NUMBER_ID: {'✓' if phone_number_id else '✗'}")
            print(f"   RECIPIENT: {'✓' if recipient else '✗'}")
            return False

        # Prepare message
        message = """🚀 *Digital Employee System - LIVE LAUNCH!* 🎉

Hello! 👋

This is the Digital Employee System, and I'm thrilled to announce that we are now LIVE and operational!

✨ *What's Now Live:*

🤖 Intelligent Automation
📧 Email Integration (Gmail API)
📱 Social Media Management
💬 WhatsApp Messaging
📊 Real-time Dashboard
✅ Health Monitoring & Alerts

🎯 *Key Features:*
• AI-Powered Task Automation
• Multi-Channel Integration
• Human-in-the-Loop Approvals
• Real-time Monitoring

🚀 The future of business automation is HERE!

Thank you for your support!"""

        print(f"\n📝 WhatsApp Message:\n{message}\n")

        # Send via WhatsApp Business API
        url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "body": message
            }
        }

        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and "messages" in response_data:
            message_id = response_data["messages"][0]["id"]
            print(f"✅ WHATSAPP MESSAGE SENT")
            print(f"   Message ID: {message_id}")
            print(f"   Recipient: {recipient}")
            print(f"   Status: Successfully sent")
            log_action("publish_all", "whatsapp", {"message_id": message_id, "recipient": recipient, "status": "sent"}, "success")
            return True
        else:
            error_msg = response_data.get("error", {}).get("message", "Unknown error")
            print(f"❌ WhatsApp API Error: {error_msg}")
            print(f"   Response: {response_data}")
            log_action("publish_all", "whatsapp", {"error": error_msg, "status": "failed"}, "error")
            return False

    except ImportError:
        print("⚠️  requests not installed. Run: uv add requests")
        return False
    except Exception as e:
        print(f"❌ WhatsApp Error: {str(e)}")
        log_action("publish_all", "whatsapp", {"error": str(e)}, "error")
        return False


# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    print("\n" + "="*90)
    print("🚀 MULTI-PLATFORM PUBLICATION SYSTEM")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*90)

    results = {
        "twitter": publish_to_twitter(),
        "linkedin": publish_to_linkedin(),
        "facebook": publish_to_facebook(),
        "whatsapp": send_whatsapp_message()
    }

    # Summary
    print("\n" + "="*90)
    print("📊 PUBLICATION SUMMARY")
    print("="*90)
    for platform, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{platform.upper():15} {status}")

    total = sum(results.values())
    print(f"\n{total}/4 platforms published successfully")

    if total == 4:
        print("\n🎉 ALL PLATFORMS PUBLISHED SUCCESSFULLY!")

    print("="*90)
