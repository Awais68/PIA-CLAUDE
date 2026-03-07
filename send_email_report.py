#!/usr/bin/env python3
"""
Send email report using Gmail API
"""

import os
import sys
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load broader scopes for sending
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly',
]

def send_email_report(recipient: str, results: list):
    """Send email report with publishing results"""
    project_root = Path(__file__).parent
    token_path = project_root / "token.json"
    credentials_path = project_root / "credentials.json"
    
    if not token_path.exists():
        print("❌ token.json not found")
        return False
    
    if not credentials_path.exists():
        print("❌ credentials.json not found")
        return False
    
    try:
        # Load credentials
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # Refresh if expired
        if creds.expired:
            creds.refresh(Request())
        
        # Build service
        service = build('gmail', 'v1', credentials=creds)
        
        # Create email content
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subject = f"🚀 Zoya Multi-Platform Publishing Report - {timestamp}"
        
        # Count results
        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success
        
        # Generate HTML report
        rows = ""
        for r in results:
            status_icon = "✅" if r['success'] else "❌"
            status_text = "SUCCESS" if r['success'] else "FAILED"
            url_html = f'<br><a href="{r["url"]}" target="_blank">View Post</a>' if r.get('url') else ""
            rows += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{r['platform'].upper()}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{status_icon} {status_text}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{r['message']}{url_html}</td>
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
        
        # Create message
        message = MIMEMultipart('alternative')
        message['to'] = recipient
        message['from'] = 'Zoya AI Employee <me>'
        message['subject'] = subject
        
        # Plain text version
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
        for r in results:
            status = "✅ SUCCESS" if r['success'] else "❌ FAILED"
            text_body += f"\n{r['platform'].upper()}: {status}\n  {r['message']}\n"
            if r.get('url'):
                text_body += f"  URL: {r['url']}\n"
        
        text_body += f"\n{'-'*60}\n\nZoya AI Employee System\nEnterprise Automation Made Simple\n"
        
        message.attach(MIMEText(text_body, 'plain'))
        message.attach(MIMEText(html_body, 'html'))
        
        # Encode and send
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        result = (
            service.users()
            .messages()
            .send(userId='me', body={'raw': raw_message})
            .execute()
        )
        
        print(f"✅ Email sent successfully! Message ID: {result['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


if __name__ == '__main__':
    # Test with sample results
    test_results = [
        {'platform': 'twitter', 'success': False, 'message': 'Invalid credentials (401)'},
        {'platform': 'linkedin', 'success': False, 'message': 'URN mismatch'},
        {'platform': 'facebook', 'success': False, 'message': 'Group posting issue'},
        {'platform': 'whatsapp', 'success': False, 'message': 'Invalid token'},
        {'platform': 'gmail', 'success': True, 'message': 'Email sent'},
    ]
    
    recipient = sys.argv[1] if len(sys.argv) > 1 else 'awaisniaz720@gmail.com'
    send_email_report(recipient, test_results)
