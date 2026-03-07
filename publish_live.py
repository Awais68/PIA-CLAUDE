#!/usr/bin/env python3
"""
🚀 Zoya - Live Multi-Platform Publisher
Posts to Twitter, LinkedIn, Facebook, WhatsApp and sends email report
"""

import os
import sys
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent / "src"))

import requests
from dotenv import load_dotenv

load_dotenv()

@dataclass
class PlatformResult:
    platform: str
    success: bool
    message: str
    post_id: str = ""
    url: str = ""

class ZoyaLivePublisher:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results: List[PlatformResult] = []
        
        # Load credentials from .env
        self.twitter_config = {
            'bearer_token': os.getenv('TWITTER_BEARER_TOKEN', ''),
            'api_key': os.getenv('TWITTER_API_KEY', ''),
            'api_secret': os.getenv('TWITTER_API_SECRET', ''),
            'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
            'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', ''),
        }
        
        self.linkedin_config = {
            'access_token': os.getenv('LINKEDIN_ACCESS_TOKEN', ''),
            'person_urn': os.getenv('LINKEDIN_PERSON_URN', ''),
        }
        
        self.facebook_config = {
            'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN', ''),
            'page_id': os.getenv('FACEBOOK_PAGE_ID', ''),
        }
        
        self.whatsapp_config = {
            'access_token': os.getenv('WHATSAPP_ACCESS_TOKEN', ''),
            'phone_number_id': os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''),
            'recipient': os.getenv('OWNER_WHATSAPP_NUMBER', '+92-335-2204606').replace('-', ''),
        }
        
        print("📋 Loaded credentials:")
        print(f"   Twitter Bearer: {'✓' if self.twitter_config['bearer_token'] else '✗'}")
        print(f"   LinkedIn Token: {'✓' if self.linkedin_config['access_token'] else '✗'}")
        print(f"   Facebook Token: {'✓' if self.facebook_config['access_token'] else '✗'}")
        print(f"   WhatsApp Token: {'✓' if self.whatsapp_config['access_token'] else '✗'}")
        print()

    def publish_to_twitter(self):
        """Post to Twitter using API v2"""
        print("\n" + "="*80)
        print("🐦 TWITTER")
        print("="*80)
        
        content = """🤖 Built an AI that processes 60+ documents without cloud.
Multi-channel ingestion, HITL approval, complete audit trail.
This is enterprise automation.

#AI #Automation #Python #LocalFirst #BusinessTech"""
        
        if not self.twitter_config['bearer_token']:
            self.results.append(PlatformResult('twitter', False, 'Missing bearer token'))
            print("❌ Missing bearer token")
            return
        
        url = "https://api.twitter.com/2/tweets"
        headers = {
            "Authorization": f"Bearer {self.twitter_config['bearer_token']}",
            "Content-Type": "application/json"
        }
        
        payload = {"text": content}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                if 'data' in data and 'id' in data['data']:
                    tweet_id = data['data']['id']
                    self.results.append(PlatformResult(
                        'twitter', True, 'Successfully posted',
                        post_id=tweet_id,
                        url=f"https://twitter.com/i/web/status/{tweet_id}"
                    ))
                    print(f"✅ SUCCESS: Posted! URL: https://twitter.com/i/web/status/{tweet_id}")
                    return
            
            # Handle error
            error_data = response.json()
            error_msg = error_data.get('error', 'Unknown error')
            if 'errors' in error_data and len(error_data['errors']) > 0:
                error_msg = error_data['errors'][0].get('message', error_msg)
            
            self.results.append(PlatformResult('twitter', False, str(error_msg)[:150]))
            print(f"❌ FAILED: {error_msg}")
            
        except Exception as e:
            self.results.append(PlatformResult('twitter', False, str(e)[:150]))
            print(f"❌ ERROR: {e}")

    def publish_to_linkedin(self):
        """Post to LinkedIn"""
        print("\n" + "="*80)
        print("💼 LINKEDIN")
        print("="*80)
        
        content = """🚀 Excited to share Zoya - My Personal AI Employee

I've built an autonomous AI system that manages business operations end-to-end:

✅ Document Processing (invoices, contracts, emails)
✅ Multi-channel Integration (Gmail, WhatsApp, Social Media)
✅ Human-in-the-Loop Approvals
✅ Complete Audit Trail
✅ Self-Monitoring & Health Checks

Key Achievements:
📊 60+ documents processed
✅ 100% success rate
⚡ 45-60 seconds per document
🔐 Zero cloud dependencies

The future of work is autonomous AI with proper structure and good engineering.

#AI #Automation #PersonalAI #BusinessAutomation #Innovation #TechLeadership"""
        
        if not self.linkedin_config['access_token']:
            self.results.append(PlatformResult('linkedin', False, 'Missing access token'))
            print("❌ Missing access token")
            return
        
        person_urn = self.linkedin_config['person_urn']
        if not person_urn:
            self.results.append(PlatformResult('linkedin', False, 'Missing person URN'))
            print("❌ Missing person URN")
            return
        
        print(f"Using Person URN: {person_urn}")
        
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {self.linkedin_config['access_token']}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202402"
        }
        
        # Fix: Use correct URN format - must be urn:li:person:NUMBER not urn:li:person:STRING
        # Extract numeric ID if possible, or use member URN
        author_urn = person_urn
        if person_urn == "urn:li:person:8IRaaon79y":
            # This is a string ID, need to convert or use member URN format
            # Try using member URN instead
            author_urn = "urn:li:member:8IRaaon79y"
        
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                if 'id' in data:
                    post_id = data['id']
                    self.results.append(PlatformResult(
                        'linkedin', True, 'Successfully posted',
                        post_id=post_id,
                        url=f"https://www.linkedin.com/feed/update/{post_id}"
                    ))
                    print(f"✅ SUCCESS: Posted! URL: https://www.linkedin.com/feed/update/{post_id}")
                    return
            
            # Handle error
            error_data = response.json()
            error_msg = error_data.get('message', error_data.get('error', 'Unknown error'))
            self.results.append(PlatformResult('linkedin', False, str(error_msg)[:150]))
            print(f"❌ FAILED: {error_msg}")
            
        except Exception as e:
            self.results.append(PlatformResult('linkedin', False, str(e)[:150]))
            print(f"❌ ERROR: {e}")

    def publish_to_facebook(self):
        """Post to Facebook Page"""
        print("\n" + "="*80)
        print("📘 FACEBOOK")
        print("="*80)
        
        content = """🚀 Announcing the Launch of Digital Employee System

I'm thrilled to share that the Digital Employee System is now officially LIVE!

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

#DigitalEmployee #AI #Automation #FutureOfWork #BusinessTech #Innovation #Founder"""
        
        if not self.facebook_config['access_token']:
            self.results.append(PlatformResult('facebook', False, 'Missing access token'))
            print("❌ Missing access token")
            return
        
        page_id = self.facebook_config['page_id']
        if not page_id:
            self.results.append(PlatformResult('facebook', False, 'Missing page ID'))
            print("❌ Missing page ID")
            return
        
        print(f"Posting to Page ID: {page_id}")
        
        # Post to page feed
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        params = {
            "message": content,
            "access_token": self.facebook_config['access_token']
        }
        
        try:
            response = requests.post(url, data=params, timeout=30)
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'id' in data:
                    post_id = data['id']
                    self.results.append(PlatformResult(
                        'facebook', True, 'Successfully posted',
                        post_id=post_id,
                        url=f"https://www.facebook.com/{page_id}/posts/{post_id.split('_')[1] if '_' in post_id else post_id}"
                    ))
                    print(f"✅ SUCCESS: Posted! Post ID: {post_id}")
                    return
            
            # Handle error
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            self.results.append(PlatformResult('facebook', False, str(error_msg)[:150]))
            print(f"❌ FAILED: {error_msg}")
            
        except Exception as e:
            self.results.append(PlatformResult('facebook', False, str(e)[:150]))
            print(f"❌ ERROR: {e}")

    def send_whatsapp_message(self):
        """Send WhatsApp message"""
        print("\n" + "="*80)
        print("💬 WHATSAPP")
        print("="*80)
        
        content = """🚀 *Digital Employee System - LIVE LAUNCH!* 🎉

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
        
        if not self.whatsapp_config['access_token']:
            self.results.append(PlatformResult('whatsapp', False, 'Missing access token'))
            print("❌ Missing access token")
            return
        
        phone_number_id = self.whatsapp_config['phone_number_id']
        if not phone_number_id:
            self.results.append(PlatformResult('whatsapp', False, 'Missing phone number ID'))
            print("❌ Missing phone number ID")
            return
        
        recipient = self.whatsapp_config['recipient']
        print(f"Sending to: {recipient}")
        
        url = f"https://graph.instagram.com/v18.0/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.whatsapp_config['access_token']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"body": content}
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if 'messages' in data and len(data['messages']) > 0:
                    message_id = data['messages'][0]['id']
                    self.results.append(PlatformResult(
                        'whatsapp', True, 'Successfully sent',
                        post_id=message_id
                    ))
                    print(f"✅ SUCCESS: Sent! Message ID: {message_id}")
                    return
            
            # Handle error
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            self.results.append(PlatformResult('whatsapp', False, str(error_msg)[:150]))
            print(f"❌ FAILED: {error_msg}")
            
        except Exception as e:
            self.results.append(PlatformResult('whatsapp', False, str(e)[:150]))
            print(f"❌ ERROR: {e}")

    def send_email_report(self, recipient: str = 'awaisais990@gmail.com'):
        """Send email report"""
        print("\n" + "="*80)
        print("📧 EMAIL REPORT")
        print("="*80)
        
        token_path = self.project_root / "token.json"
        credentials_path = self.project_root / "credentials.json"
        
        if not token_path.exists():
            self.results.append(PlatformResult('gmail', False, 'token.json not found'))
            print("❌ token.json not found")
            return
        
        if not credentials_path.exists():
            self.results.append(PlatformResult('gmail', False, 'credentials.json not found'))
            print("❌ credentials.json not found")
            return
        
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.modify',
            ]
            
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            
            if creds.expired:
                print("Refreshing expired token...")
                creds.refresh(Request())
            
            service = build('gmail', 'v1', credentials=creds)
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            subject = f"🚀 Zoya Multi-Platform Publishing Report - {timestamp}"
            
            # Count results
            total = len(self.results)
            success = sum(1 for r in self.results if r.success)
            failed = total - success
            
            # Generate HTML
            rows = ""
            for r in self.results:
                status_icon = "✅" if r.success else "❌"
                status_text = "SUCCESS" if r.success else "FAILED"
                url_html = f'<br><a href="{r.url}" target="_blank">View Post</a>' if r.url else ""
                rows += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">{r.platform.upper()}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{status_icon} {status_text}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{r.message}{url_html}</td>
                </tr>
                """
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .failed {{ color: #dc3545; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border: 1px solid #ddd; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Zoya Multi-Platform Publishing Report</h1>
        <p>Generated: {timestamp}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <p><span class="success">✅ Successful: {success}</span> | <span class="failed">❌ Failed: {failed}</span> | Total: {total}</p>
        <p>Success Rate: {(success/total*100) if total > 0 else 0:.0f}%</p>
    </div>
    
    <h2>📱 Platform Results</h2>
    <table>
        <tr>
            <th>Platform</th>
            <th>Status</th>
            <th>Details</th>
        </tr>
        {rows}
    </table>
    
    <div class="footer">
        <p><strong>Zoya AI Employee System</strong><br>
        Enterprise Automation Made Simple<br>
        Powered by Claude Code + Local-First Architecture</p>
    </div>
</body>
</html>
"""
            
            message = MIMEMultipart('alternative')
            message['to'] = recipient
            message['from'] = 'Zoya AI Employee <me>'
            message['subject'] = subject
            
            text_body = f"""🚀 ZOYA MULTI-PLATFORM PUBLISHING REPORT
Generated: {timestamp}

📊 SUMMARY
✅ Successful: {success}
❌ Failed: {failed}
Total: {total}
Success Rate: {(success/total*100) if total > 0 else 0:.0f}%

📱 PLATFORM RESULTS
{'-'*60}
"""
            for r in self.results:
                status = "✅ SUCCESS" if r.success else "❌ FAILED"
                text_body += f"\n{r.platform.upper()}: {status}\n  {r.message}\n"
                if r.url:
                    text_body += f"  URL: {r.url}\n"
            
            text_body += f"\n{'-'*60}\n\nZoya AI Employee System\nEnterprise Automation Made Simple\n"
            
            message.attach(MIMEText(text_body, 'plain'))
            message.attach(MIMEText(html_body, 'html'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = (
                service.users()
                .messages()
                .send(userId='me', body={'raw': raw_message})
                .execute()
            )
            
            self.results.append(PlatformResult(
                'gmail', True, 'Report sent successfully',
                post_id=result['id']
            ))
            print(f"✅ SUCCESS: Email sent! Message ID: {result['id']}")
            
        except Exception as e:
            self.results.append(PlatformResult('gmail', False, str(e)[:150]))
            print(f"❌ FAILED: {e}")

    def run_all(self, email_recipient: str = 'awaisais990@gmail.com'):
        """Run all publishing tasks"""
        print("\n" + "="*80)
        print("🚀 ZOYA MULTI-PLATFORM PUBLISHING SYSTEM - LIVE")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        self.publish_to_twitter()
        self.publish_to_linkedin()
        self.publish_to_facebook()
        self.send_whatsapp_message()
        self.send_email_report(email_recipient)
        
        # Summary
        print("\n" + "="*80)
        print("📊 FINAL SUMMARY")
        print("="*80)
        
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        
        for r in self.results:
            status = "✅ SUCCESS" if r.success else "❌ FAILED"
            print(f"{r.platform.upper():15} {status}")
            if r.url:
                print(f"                {r.url}")
        
        print(f"\n{success}/{total} platforms published successfully")
        print(f"Success Rate: {success/total*100:.0f}%")
        
        if success == total:
            print("\n🎉 ALL PLATFORMS PUBLISHED SUCCESSFULLY!")
        elif success > 0:
            print(f"\n⚠️  {total - success} platform(s) had issues")
        else:
            print("\n❌ All platforms failed")
        
        print("="*80)
        
        return success == total


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Zoya Multi-Platform Publisher')
    parser.add_argument('--email', '-e', default='awaisais990@gmail.com',
                       help='Email address for report')
    args = parser.parse_args()
    
    publisher = ZoyaLivePublisher()
    success = publisher.run_all(args.email)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
