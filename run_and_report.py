#!/usr/bin/env python3
"""
🚀 Zoya - Run Multi-Platform Post & Send Report
Posts to all integrated social media accounts, sends WhatsApp messages, and emails a report.
"""

import os
import sys
import re
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class PlatformResult:
    """Result from posting to a platform"""
    platform: str
    success: bool
    message: str
    post_id: str = ""
    url: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ZoyaPublisher:
    """Multi-platform publisher for Zoya AI Employee"""

    def __init__(self):
        self.results: List[PlatformResult] = []
        self.project_root = Path(__file__).parent
        self.vault_path = self.project_root / "AI_Employee_Vault"
        
        # Load credentials
        self.config = {
            'twitter': self._load_twitter_config(),
            'linkedin': self._load_linkedin_config(),
            'facebook': self._load_facebook_config(),
            'whatsapp': self._load_whatsapp_config(),
            'gmail': self._load_gmail_config(),
        }
        
        # Content to post
        self.content = self._load_content()

    def _load_twitter_config(self) -> Dict:
        return {
            'api_key': os.getenv('TWITTER_API_KEY', ''),
            'api_secret': os.getenv('TWITTER_API_SECRET', ''),
            'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
            'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET', ''),
        }

    def _load_linkedin_config(self) -> Dict:
        return {
            'client_id': os.getenv('LINKEDIN_CLIENT_ID', ''),
            'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET', ''),
            'access_token': os.getenv('LINKEDIN_ACCESS_TOKEN', ''),
            'person_urn': os.getenv('LINKEDIN_PERSON_URN', ''),
        }

    def _load_facebook_config(self) -> Dict:
        return {
            'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN', ''),
            'page_id': os.getenv('FACEBOOK_PAGE_ID', ''),
        }

    def _load_whatsapp_config(self) -> Dict:
        return {
            'access_token': os.getenv('WHATSAPP_ACCESS_TOKEN', ''),
            'phone_number_id': os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''),
            'recipient': os.getenv('OWNER_WHATSAPP_NUMBER', '+92-335-2204606'),
        }

    def _load_gmail_config(self) -> Dict:
        return {
            'credentials_path': self.project_root / 'credentials.json',
            'token_path': self.project_root / 'token.json',
        }

    def _load_content(self) -> Dict:
        """Load content to post from SOCIAL_MEDIA_POSTS.md or use defaults"""
        posts_file = self.project_root / "SOCIAL_MEDIA_POSTS.md"
        
        default_content = {
            'twitter': """🤖 Built an AI that processes 60+ documents without cloud.
Multi-channel ingestion, HITL approval, complete audit trail.
This is enterprise automation.

#AI #Automation #Python #LocalFirst #BusinessTech""",
            
            'linkedin': """🚀 Excited to share Zoya - My Personal AI Employee

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

#AI #Automation #PersonalAI #BusinessAutomation #Innovation #TechLeadership""",
            
            'facebook': """🚀 Announcing the Launch of Digital Employee System

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

#DigitalEmployee #AI #Automation #FutureOfWork #BusinessTech #Innovation #Founder""",
            
            'whatsapp': """🚀 *Digital Employee System - LIVE LAUNCH!* 🎉

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

Thank you for your support!""",
        }
        
        if posts_file.exists():
            print(f"📄 Found content file: {posts_file.name}")
            # Could parse the file for actual content
            # For now, use defaults which are well-formatted
        
        return default_content

    def log_result(self, platform: str, success: bool, message: str, **kwargs):
        """Log a publishing result"""
        result = PlatformResult(
            platform=platform,
            success=success,
            message=message,
            **kwargs
        )
        self.results.append(result)
        
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status} {platform.upper():12} | {message}")

    # ============================================================================
    # TWITTER
    # ============================================================================

    def publish_to_twitter(self) -> bool:
        """Post to Twitter using tweepy"""
        print("\n" + "="*90)
        print("🐦 PUBLISHING TO TWITTER")
        print("="*90)

        config = self.config['twitter']
        
        # Check credentials
        if not all([config['api_key'], config['api_secret'], 
                   config['access_token'], config['access_token_secret']]):
            self.log_result('twitter', False, 'Missing credentials')
            return False

        try:
            import tweepy

            # Initialize OAuth 1.0a
            auth = tweepy.OAuthHandler(config['api_key'], config['api_secret'])
            auth.set_access_token(config['access_token'], config['access_token_secret'])
            api = tweepy.API(auth)

            # Get content
            content = self.content['twitter']
            print(f"\n📝 Tweet Content:\n{content}\n")

            # Post tweet
            result = api.update_status(status=content)

            self.log_result(
                'twitter', True, 'Successfully posted',
                post_id=str(result.id),
                url=f"https://twitter.com/i/web/status/{result.id}"
            )
            return True

        except ImportError:
            self.log_result('twitter', False, 'tweepy not installed')
            return False
        except Exception as e:
            error_msg = str(e)
            if '402' in error_msg or 'Payment' in error_msg:
                self.log_result('twitter', False, 'API requires payment/upgrade (402)')
            elif '401' in error_msg:
                self.log_result('twitter', False, 'Invalid credentials (401)')
            else:
                self.log_result('twitter', False, f'API Error: {error_msg[:80]}')
            return False

    # ============================================================================
    # LINKEDIN
    # ============================================================================

    def publish_to_linkedin(self) -> bool:
        """Post to LinkedIn using their API"""
        print("\n" + "="*90)
        print("💼 PUBLISHING TO LINKEDIN")
        print("="*90)

        config = self.config['linkedin']
        
        if not config['access_token'] or not config['person_urn']:
            self.log_result('linkedin', False, 'Missing credentials')
            return False

        try:
            content = self.content['linkedin']
            print(f"\n📝 LinkedIn Post:\n{content[:300]}...\n")

            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {config['access_token']}",
                "Content-Type": "application/json"
            }

            payload = {
                "author": config['person_urn'],
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
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
                self.log_result(
                    'linkedin', True, 'Successfully posted',
                    post_id=post_id,
                    url=f"https://www.linkedin.com/feed/update/{post_id}"
                )
                return True
            else:
                error_msg = response_data.get('message', response_data.get('error', 'Unknown error'))
                if '403' in str(response.status_code) or 'insufficient' in str(error_msg).lower():
                    self.log_result('linkedin', False, 'Insufficient permissions (403) - Token needs refresh')
                else:
                    self.log_result('linkedin', False, f'API Error: {str(error_msg)[:80]}')
                return False

        except Exception as e:
            self.log_result('linkedin', False, f'Error: {str(e)[:80]}')
            return False

    # ============================================================================
    # FACEBOOK
    # ============================================================================

    def publish_to_facebook(self) -> bool:
        """Post to Facebook using Graph API"""
        print("\n" + "="*90)
        print("📱 PUBLISHING TO FACEBOOK")
        print("="*90)

        config = self.config['facebook']
        
        if not config['access_token'] or not config['page_id']:
            self.log_result('facebook', False, 'Missing credentials')
            return False

        try:
            content = self.content['facebook']
            print(f"\n📝 Facebook Post:\n{content[:300]}...\n")

            url = f"https://graph.facebook.com/v18.0/{config['page_id']}/feed"
            params = {
                "message": content,
                "access_token": config['access_token']
            }

            response = requests.post(url, data=params)
            response_data = response.json()

            if response.status_code == 200 and "id" in response_data:
                post_id = response_data["id"]
                self.log_result(
                    'facebook', True, 'Successfully posted',
                    post_id=post_id,
                    url=f"https://www.facebook.com/{config['page_id']}/posts/{post_id.split('_')[1] if '_' in post_id else post_id}"
                )
                return True
            else:
                error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                self.log_result('facebook', False, f'API Error: {str(error_msg)[:80]}')
                return False

        except Exception as e:
            self.log_result('facebook', False, f'Error: {str(e)[:80]}')
            return False

    # ============================================================================
    # WHATSAPP
    # ============================================================================

    def send_whatsapp_message(self) -> bool:
        """Send WhatsApp message via Business API"""
        print("\n" + "="*90)
        print("💬 SENDING WHATSAPP MESSAGE")
        print("="*90)

        config = self.config['whatsapp']
        
        if not all([config['access_token'], config['phone_number_id'], config['recipient']]):
            self.log_result('whatsapp', False, 'Missing credentials')
            return False

        try:
            message = self.content['whatsapp']
            print(f"\n📝 WhatsApp Message:\n{message}\n")

            # Clean recipient number (remove dashes)
            recipient = config['recipient'].replace('-', '')

            url = f"https://graph.instagram.com/v18.0/{config['phone_number_id']}/messages"
            headers = {
                "Authorization": f"Bearer {config['access_token']}",
                "Content-Type": "application/json"
            }

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "text",
                "text": {"body": message}
            }

            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 200 and "messages" in response_data:
                message_id = response_data["messages"][0]["id"]
                self.log_result(
                    'whatsapp', True, 'Successfully sent',
                    message_id=message_id,
                    post_id=message_id
                )
                return True
            else:
                error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                if '136027' in str(response_data) or 'token' in str(error_msg).lower():
                    self.log_result('whatsapp', False, 'Invalid token - needs refresh')
                else:
                    self.log_result('whatsapp', False, f'API Error: {str(error_msg)[:80]}')
                return False

        except Exception as e:
            self.log_result('whatsapp', False, f'Error: {str(e)[:80]}')
            return False

    # ============================================================================
    # GMAIL - SEND EMAIL REPORT
    # ============================================================================

    def send_email_report(self, recipient: str = None) -> bool:
        """Send email report with publishing results"""
        print("\n" + "="*90)
        print("📧 SENDING EMAIL REPORT")
        print("="*90)

        if not recipient:
            # Try to get from environment or use default
            recipient = os.getenv('REPORT_EMAIL', 'awaisniaz720@gmail.com')

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            token_path = self.config['gmail']['token_path']
            credentials_path = self.config['gmail']['credentials_path']

            if not token_path.exists():
                self.log_result('gmail', False, 'token.json not found - need to authenticate')
                return False

            if not credentials_path.exists():
                self.log_result('gmail', False, 'credentials.json not found')
                return False

            # Load credentials
            SCOPES = ['https://www.googleapis.com/auth/gmail.send']
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

            # Refresh if expired
            if creds.expired:
                from google.auth.transport.requests import Request
                creds.refresh(Request())

            # Build service
            service = build('gmail', 'v1', credentials=creds)

            # Create email content
            subject = f"🚀 Zoya Multi-Platform Publishing Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Generate HTML report
            html_body = self._generate_email_report_html()
            
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = recipient
            message['from'] = 'Zoya AI Employee <me>'
            message['subject'] = subject

            # Plain text version
            text_body = self._generate_email_report_text()
            message.attach(MIMEText(text_body, 'plain'))
            
            # HTML version
            message.attach(MIMEText(html_body, 'html'))

            # Encode and send
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = (
                service.users()
                .messages()
                .send(userId='me', body={'raw': raw_message})
                .execute()
            )

            self.log_result(
                'gmail', True, 'Report sent successfully',
                post_id=result['id']
            )
            return True

        except ImportError as e:
            self.log_result('gmail', False, f'Missing dependency: {str(e)[:50]}')
            return False
        except FileNotFoundError:
            self.log_result('gmail', False, 'Gmail credentials not found')
            return False
        except Exception as e:
            error_msg = str(e)
            if 'invalid_scope' in error_msg.lower():
                self.log_result('gmail', False, 'Invalid OAuth scope - needs re-authentication')
            elif 'token_expired' in error_msg.lower() or 'invalid_grant' in error_msg.lower():
                self.log_result('gmail', False, 'Token expired - needs re-authentication')
            else:
                self.log_result('gmail', False, f'Error: {error_msg[:80]}')
            return False

    def _generate_email_report_html(self) -> str:
        """Generate HTML email report"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Count results
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success
        
        # Generate platform rows
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

        html = f"""
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
        return html

    def _generate_email_report_text(self) -> str:
        """Generate plain text email report"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success
        
        lines = [
            "🚀 ZOYA MULTI-PLATFORM PUBLISHING REPORT",
            f"Generated: {timestamp}",
            "",
            "📊 SUMMARY",
            f"✅ Successful: {success}",
            f"❌ Failed: {failed}",
            f"Total: {total}",
            f"Success Rate: {(success/total*100) if total > 0 else 0:.0f}%",
            "",
            "📱 PLATFORM RESULTS",
            "-" * 60,
        ]
        
        for r in self.results:
            status = "✅ SUCCESS" if r.success else "❌ FAILED"
            lines.append(f"\n{r.platform.upper()}: {status}")
            lines.append(f"  {r.message}")
            if r.url:
                lines.append(f"  URL: {r.url}")
        
        lines.extend([
            "",
            "-" * 60,
            "",
            "Zoya AI Employee System",
            "Enterprise Automation Made Simple",
            "Powered by Claude Code + Local-First Architecture",
        ])
        
        return "\n".join(lines)

    # ============================================================================
    # MAIN EXECUTION
    # ============================================================================

    def run_all(self, email_recipient: str = None):
        """Run all publishing tasks"""
        print("\n" + "="*90)
        print("🚀 ZOYA MULTI-PLATFORM PUBLISHING SYSTEM")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*90)

        # Run all platforms
        self.publish_to_twitter()
        self.publish_to_linkedin()
        self.publish_to_facebook()
        self.send_whatsapp_message()
        
        # Send email report (must be last to include all results)
        self.send_email_report(email_recipient)

        # Final Summary
        print("\n" + "="*90)
        print("📊 FINAL PUBLISHING SUMMARY")
        print("="*90)
        
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
            print(f"\n⚠️  {total - success} platform(s) failed. Check credentials.")
        else:
            print("\n❌ All platforms failed. Check credentials and try again.")
        
        print("="*90)
        
        return success == total


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Zoya Multi-Platform Publisher')
    parser.add_argument('--email', '-e', help='Email address for report', 
                       default='awaisniaz720@gmail.com')
    args = parser.parse_args()

    publisher = ZoyaPublisher()
    success = publisher.run_all(email_recipient=args.email)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
