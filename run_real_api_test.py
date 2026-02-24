#!/usr/bin/env python3
"""
Simplified Real API Integration Test
Tests all 6 MCP servers with actual API calls
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

print("\n" + "╔" + "="*78 + "╗")
print("║" + " "*20 + "REAL API INTEGRATION TEST" + " "*33 + "║")
print("║" + " "*15 + "Testing All 6 Services with Real APIs" + " "*26 + "║")
print("╚" + "="*78 + "╝\n")

# Test counters
tests_passed = 0
tests_failed = 0

# ============================================================================
# TEST 1: Gmail API
# ============================================================================
print("📧 TEST 1: Gmail API - Sending Real Email")
print("-" * 80)
try:
    import pickle
    import base64
    from email.mime.text import MIMEText
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    credentials_file = PROJECT_ROOT / "credentials.json"
    token_file = PROJECT_ROOT / "token.json"
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']

    credentials = None
    if token_file.exists():
        with open(token_file, 'rb') as token:
            credentials = pickle.load(token)

    if credentials and credentials.expired:
        credentials.refresh(Request())

    if not credentials and not credentials_file.exists():
        print("⚠️  Gmail credentials.json not found - skipping Gmail test")
        tests_failed += 1
    elif credentials or credentials_file.exists():
        if not credentials:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES)
            credentials = flow.run_local_server(port=0)
            with open(token_file, 'wb') as token:
                pickle.dump(credentials, token)

        service = build('gmail', 'v1', credentials=credentials)

        message = MIMEText("This is a test email from Zoya AI Employee System")
        message['to'] = os.getenv("TEST_EMAIL_RECIPIENT", "test@example.com")
        message['subject'] = f"Zoya Test - {datetime.now().isoformat()}"

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = {'raw': raw}

        result = service.users().messages().send(userId='me', body=send_message).execute()

        if result and result.get('id'):
            print(f"✅ Email sent successfully! Message ID: {result['id']}")
            tests_passed += 1
        else:
            print("❌ Email sent but no ID returned")
            tests_failed += 1

except ImportError as e:
    print(f"⚠️  Skipping Gmail test (dependency missing: {e})")
    tests_failed += 1
except Exception as e:
    print(f"❌ Gmail test failed: {e}")
    tests_failed += 1

# ============================================================================
# TEST 2: Twitter API v2
# ============================================================================
print("\n🐦 TEST 2: Twitter/X API v2 - Posting Real Tweet")
print("-" * 80)
try:
    import tweepy

    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("⚠️  Twitter credentials not configured - skipping Twitter test")
        tests_failed += 1
    else:
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
            wait_on_rate_limit=True
        )

        me = client.get_me()
        if me:
            tweet_text = f"🤖 Zoya AI Test Tweet - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} #AI #Automation"
            response = client.create_tweet(text=tweet_text)

            if response and response.data:
                print(f"✅ Tweet posted successfully! Tweet ID: {response.data['id']}")
                tests_passed += 1
            else:
                print("❌ Tweet creation returned no data")
                tests_failed += 1
        else:
            print("❌ Failed to authenticate with Twitter")
            tests_failed += 1

except ImportError as e:
    print(f"⚠️  Skipping Twitter test (dependency missing)")
    tests_failed += 1
except Exception as e:
    print(f"❌ Twitter test failed: {e}")
    tests_failed += 1

# ============================================================================
# TEST 3: LinkedIn API v2
# ============================================================================
print("\n💼 TEST 3: LinkedIn API v2 - Posting to Company Page")
print("-" * 80)
try:
    import requests

    linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    linkedin_page_id = os.getenv("LINKEDIN_PAGE_ID")

    if not linkedin_token or not linkedin_page_id:
        print("⚠️  LinkedIn credentials not configured - skipping LinkedIn test")
        tests_failed += 1
    else:
        headers = {
            "Authorization": f"Bearer {linkedin_token}",
            "Content-Type": "application/json"
        }

        post_content = {
            "commentary": {
                "text": f"🚀 Zoya AI Test Post - {datetime.now().isoformat()} #AI #Automation"
            },
            "visibility": {
                "com.linkedin.ugc.visibility.MemberNetworkVisibility": "PUBLIC"
            },
            "lifecycleState": "PUBLISHED",
            "distribution": {
                "feedDistribution": "FOLLOWERS"
            }
        }

        url = f"https://api.linkedin.com/v2/ugcPosts"
        response = requests.post(url, json=post_content, headers=headers, timeout=10)

        if response.status_code in [200, 201]:
            post_id = response.json().get('id', 'unknown')
            print(f"✅ LinkedIn post created! Post ID: {post_id}")
            tests_passed += 1
        else:
            print(f"❌ LinkedIn API error: {response.status_code} - {response.text[:100]}")
            tests_failed += 1

except ImportError:
    print("⚠️  Skipping LinkedIn test (requests not available)")
    tests_failed += 1
except Exception as e:
    print(f"❌ LinkedIn test failed: {e}")
    tests_failed += 1

# ============================================================================
# TEST 4: Meta Graph API (Facebook + Instagram)
# ============================================================================
print("\n📱 TEST 4: Meta Graph API - Facebook & Instagram")
print("-" * 80)
try:
    import requests

    meta_token = os.getenv("META_ACCESS_TOKEN")
    facebook_page_id = os.getenv("FACEBOOK_PAGE_ID")
    instagram_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

    if not meta_token:
        print("⚠️  Meta credentials not configured - skipping Meta test")
        tests_failed += 1
    else:
        # Test Facebook
        if facebook_page_id:
            print("  • Testing Facebook posting...")
            payload = {
                "message": f"🤖 Zoya Test Post - {datetime.now().isoformat()} #AI",
                "access_token": meta_token
            }
            response = requests.post(
                f"https://graph.facebook.com/v18.0/{facebook_page_id}/feed",
                json=payload,
                timeout=10
            )

            if response.status_code in [200, 201]:
                post_id = response.json().get('id')
                print(f"    ✅ Facebook post created! ID: {post_id}")
                tests_passed += 1
            else:
                print(f"    ❌ Facebook error: {response.status_code}")
                tests_failed += 1
        else:
            print("  ⚠️  Facebook page ID not configured")
            tests_failed += 1

        # Test Instagram
        if instagram_id:
            print("  • Testing Instagram posting...")
            image_url = "https://via.placeholder.com/1080x1080?text=Zoya+Test"
            container_payload = {
                "image_url": image_url,
                "caption": f"🤖 Zoya Test - {datetime.now().isoformat()} #AI #Automation",
                "access_token": meta_token
            }

            response = requests.post(
                f"https://graph.instagram.com/v18.0/{instagram_id}/media",
                json=container_payload,
                timeout=10
            )

            if response.status_code in [200, 201]:
                creation_id = response.json().get('id')
                print(f"    ✅ Instagram media created! ID: {creation_id}")
                tests_passed += 1
            else:
                print(f"    ❌ Instagram error: {response.status_code}")
                tests_failed += 1
        else:
            print("  ⚠️  Instagram ID not configured")
            tests_failed += 1

except ImportError:
    print("⚠️  Skipping Meta test (requests not available)")
    tests_failed += 1
except Exception as e:
    print(f"❌ Meta test failed: {e}")
    tests_failed += 1

# ============================================================================
# TEST 5: WhatsApp Cloud API
# ============================================================================
print("\n💬 TEST 5: WhatsApp Cloud API - Sending Message")
print("-" * 80)
try:
    import requests

    whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    test_recipient = os.getenv("TEST_WHATSAPP_PHONE")

    if not whatsapp_token or not phone_number_id or not test_recipient:
        print("⚠️  WhatsApp credentials not configured - skipping WhatsApp test")
        tests_failed += 1
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": test_recipient,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": f"🤖 Zoya Test Message - {datetime.now().isoformat()}"
            }
        }

        headers = {
            "Authorization": f"Bearer {whatsapp_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"https://graph.instagram.com/v18.0/{phone_number_id}/messages",
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code in [200, 201]:
            message_id = response.json().get('messages', [{}])[0].get('id')
            print(f"✅ WhatsApp message sent! Message ID: {message_id}")
            tests_passed += 1
        else:
            print(f"❌ WhatsApp API error: {response.status_code} - {response.text[:100]}")
            tests_failed += 1

except ImportError:
    print("⚠️  Skipping WhatsApp test (requests not available)")
    tests_failed += 1
except Exception as e:
    print(f"❌ WhatsApp test failed: {e}")
    tests_failed += 1

# ============================================================================
# TEST 6: Odoo XML-RPC API
# ============================================================================
print("\n📋 TEST 6: Odoo XML-RPC - Creating Invoice")
print("-" * 80)
try:
    import xmlrpc.client

    odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
    odoo_db = os.getenv("ODOO_DB")
    odoo_user = os.getenv("ODOO_USER")
    odoo_password = os.getenv("ODOO_API_KEY")

    if not all([odoo_db, odoo_user, odoo_password]):
        print("⚠️  Odoo credentials not configured - skipping Odoo test")
        tests_failed += 1
    else:
        common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
        uid = common.authenticate(odoo_db, odoo_user, odoo_password, {})

        if uid:
            models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

            # Create partner
            partner_id = models.execute_kw(
                odoo_db, uid, odoo_password,
                'res.partner', 'create',
                [{
                    'name': f'Zoya Test - {datetime.now().isoformat()}',
                    'email': 'zoya@test.local',
                    'company_type': 'company'
                }]
            )

            # Create invoice
            invoice_id = models.execute_kw(
                odoo_db, uid, odoo_password,
                'account.move', 'create',
                [{
                    'move_type': 'out_invoice',
                    'partner_id': partner_id,
                    'invoice_date': datetime.now().strftime("%Y-%m-%d"),
                    'currency_id': 1,
                    'ref': 'Zoya Test Invoice',
                    'invoice_line_ids': [(0, 0, {
                        'product_id': 1,
                        'name': 'Test Service',
                        'quantity': 1,
                        'price_unit': 100.00
                    })]
                }]
            )

            if invoice_id:
                print(f"✅ Invoice created in Odoo! Invoice ID: {invoice_id}")
                tests_passed += 1
            else:
                print("❌ Invoice creation failed")
                tests_failed += 1
        else:
            print("❌ Failed to authenticate with Odoo")
            tests_failed += 1

except ImportError:
    print("⚠️  Skipping Odoo test (xmlrpc not available)")
    tests_failed += 1
except Exception as e:
    print(f"❌ Odoo test failed: {e}")
    tests_failed += 1

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("INTEGRATION TEST SUMMARY")
print("="*80)
print(f"\n✅ Tests Passed: {tests_passed}")
print(f"❌ Tests Failed: {tests_failed}")
print(f"⏭️  Total Tests:   {tests_passed + tests_failed}")

if tests_passed >= 4:
    print("\n🎉 SUCCESS! Multiple services are working!")
    print("\nVerify results:")
    print("  • Check your email inbox for the test email")
    print("  • Check your Twitter account for the test tweet")
    print("  • Check your LinkedIn page for the test post")
    print("  • Check your Facebook page for the test post")
    print("  • Check WhatsApp for the test message")
    print("  • Check Odoo for the test invoice")
elif tests_passed > 0:
    print(f"\n⚠️  Partial success ({tests_passed} services working)")
else:
    print("\n❌ No services successfully tested")
    print("\nChecklist:")
    print("  ✓ Is .env configured with all API credentials?")
    print("  ✓ Are the API keys valid and not expired?")
    print("  ✓ Do the API keys have the right scopes/permissions?")
    print("  ✓ Are the recipient IDs/emails configured?")

sys.exit(0 if tests_passed >= 4 else 1)
