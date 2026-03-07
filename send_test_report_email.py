#!/usr/bin/env python3
"""
Send Playwright Test Report via Gmail
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

def send_email():
    """Send test report via Gmail"""

    # Email configuration
    sender_email = os.getenv("GMAIL_EMAIL", "codetheagent1@gmail.com")
    app_password = os.getenv("GMAIL_APP_PASSWORD", "ovas erml jsot ybhk")
    recipient_email = "codetheagent1@gmail.com"

    # Report file
    report_path = Path("PLAYWRIGHT_TEST_REPORT_EMAIL.html")

    if not report_path.exists():
        print(f"❌ Report file not found: {report_path}")
        return False

    try:
        # Read HTML report
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "🎭 Playwright Test Report - codetheagent1@gmail.com"
        message["From"] = sender_email
        message["To"] = recipient_email

        # Attach HTML
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Connect to Gmail SMTP server
        print("🔗 Connecting to Gmail SMTP server...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, app_password.replace(" ", ""))

        # Send email
        print(f"📧 Sending report to {recipient_email}...")
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()

        print("✅ Email sent successfully!")
        print(f"   From: {sender_email}")
        print(f"   To: {recipient_email}")
        print(f"   Subject: 🎭 Playwright Test Report - codetheagent1@gmail.com")
        return True

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("📧 SENDING PLAYWRIGHT TEST REPORT VIA EMAIL")
    print("="*60 + "\n")

    success = send_email()

    if success:
        print("\n✨ Report has been sent to your inbox!")
        print("📍 Check: codetheagent1@gmail.com")
    else:
        print("\n⚠️  Failed to send email")
        print("   You can view the report locally at: PLAYWRIGHT_TEST_REPORT_EMAIL.html")
