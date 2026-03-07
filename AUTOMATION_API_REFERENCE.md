# Automation API Reference

## 📚 Module APIs

### LinkedIn Playwright

#### Class: `LinkedInPlaywright`

```python
from src.automations.linkedin_playwright import LinkedInPlaywright
import asyncio

async def main():
    async with LinkedInPlaywright(
        email="user@linkedin.com",
        password="password"
    ) as li:
        # Methods available
        pass
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `login()` | None | `bool` | Login to LinkedIn |
| `post_update(content, image_path=None)` | str, Optional[str] | `bool` | Post text or image update |
| `read_feed(limit=10)` | int | `List[Dict]` | Read N posts from feed |
| `like_post(post_index=0)` | int | `bool` | Like post by index |
| `send_message(recipient_name, message)` | str, str | `bool` | Send DM to contact |
| `close()` | None | None | Close browser |

#### Example Response: `read_feed()`

```python
[
    {
        "author": "John Doe",
        "content": "Excited to share...",
        "likes": "245",
        "comments": "12",
        "timestamp": "2026-03-07T10:30:00"
    }
]
```

---

### WhatsApp Playwright

#### Class: `WhatsAppPlaywright`

```python
from src.automations.whatsapp_playwright import WhatsAppPlaywright
import asyncio

async def main():
    async with WhatsAppPlaywright(headless=False) as wa:
        # Methods available
        pass
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `login()` | None | `bool` | Login (shows QR for first time) |
| `send_message(contact_name, message)` | str, str | `bool` | Send text message |
| `read_messages(contact_name, limit=10)` | str, int | `List[Dict]` | Read message history |
| `send_media(contact_name, media_path, caption="")` | str, str, str | `bool` | Send image/video |
| `react_to_message(emoji)` | str | `bool` | React with emoji |
| `get_status(contact_name)` | str | `Optional[str]` | Get last seen/status |
| `close()` | None | None | Close browser |

#### Example Response: `read_messages()`

```python
[
    {
        "sender": "Mom",
        "text": "Hi sweetheart!",
        "time": "10:30 AM",
        "timestamp": "2026-03-07T10:30:00"
    },
    {
        "sender": "Me",
        "text": "Hi Mom!",
        "time": "10:31 AM",
        "timestamp": "2026-03-07T10:31:00"
    }
]
```

---

### Gmail App Password

#### Class: `GmailAppPassword`

```python
from src.automations.gmail_app_password import GmailAppPassword
import os

gmail = GmailAppPassword(
    email=os.getenv("GMAIL_EMAIL"),
    app_password=os.getenv("GMAIL_APP_PASSWORD")
)

# Use methods
try:
    # ... do stuff
    pass
finally:
    gmail.close()
```

#### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `send_email(to, subject, body, attachments=None, is_html=False)` | str, str, str, List[str], bool | `bool` | Send email |
| `read_emails(folder="INBOX", limit=10, unread_only=False)` | str, int, bool | `List[Dict]` | Read emails |
| `search_emails(query, folder="INBOX", limit=20)` | str, str, int | `List[Dict]` | Search emails |
| `create_draft(to, subject, body)` | str, str, str | `bool` | Create draft |
| `mark_as_read(message_ids)` | List[int] | `bool` | Mark as read |
| `delete_email(message_ids)` | List[int] | `bool` | Delete emails |
| `add_label(message_ids, label)` | List[int], str | `bool` | Add label/folder |
| `archive_email(message_ids)` | List[int] | `bool` | Archive emails |
| `move_to_spam(message_ids)` | List[int] | `bool` | Move to spam |
| `close()` | None | None | Close IMAP connection |

#### Example Response: `read_emails()`

```python
[
    {
        "id": 1234567890,
        "from": "boss@company.com",
        "subject": "Project Update",
        "date": "2026-03-07 10:30:00",
        "body": "Can you send me the report...",
        "timestamp": "2026-03-07T10:30:00"
    }
]
```

#### Example Response: `search_emails()`

```python
[
    {
        "id": 123,
        "from": "boss@company.com",
        "subject": "Q1 Goals",
        "date": "2026-03-01",
        "preview": "Here are the Q1 goals for the team..."
    }
]
```

---

## 🔍 Gmail Search Operators

Use with `search_emails()`:

```python
# From specific sender
gmail.search_emails("from:boss@company.com")

# To specific recipient
gmail.search_emails("to:team@company.com")

# Subject contains
gmail.search_emails("subject:meeting")

# Has attachment
gmail.search_emails("has:attachment")

# Unread only
gmail.search_emails("is:unread")

# Starred
gmail.search_emails("is:starred")

# In label
gmail.search_emails("label:important")

# Date range
gmail.search_emails("after:2026/03/01")
gmail.search_emails("before:2026/03/31")

# Text anywhere
gmail.search_emails("vacation")

# Combine (AND)
gmail.search_emails("from:boss@company.com subject:urgent")

# OR operator
gmail.search_emails("from:alice@company.com OR from:bob@company.com")
```

---

## 🎯 Complete Orchestrator Example

```python
# src/automations/daily_orchestrator.py
import asyncio
import os
import logging
from datetime import datetime
from linkedin_playwright import LinkedInPlaywright
from whatsapp_playwright import WhatsAppPlaywright
from gmail_app_password import GmailAppPassword

logger = logging.getLogger(__name__)

class DailyOrchestrator:
    def __init__(self):
        self.linkedin_email = os.getenv("LINKEDIN_EMAIL")
        self.linkedin_password = os.getenv("LINKEDIN_PASSWORD")
        self.gmail_email = os.getenv("GMAIL_EMAIL")
        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")

    async def send_morning_message(self):
        """Send good morning message on WhatsApp & LinkedIn"""
        async with WhatsAppPlaywright(headless=True) as wa:
            await wa.send_message("Family", "Good morning! ☀️")
            logger.info("✅ WhatsApp: Sent morning message")

        async with LinkedInPlaywright(self.linkedin_email, self.linkedin_password) as li:
            await li.post_update("Good morning everyone! Ready to make today count 💪")
            logger.info("✅ LinkedIn: Posted morning update")

    async def process_emails(self):
        """Process important emails"""
        gmail = GmailAppPassword(self.gmail_email, self.gmail_app_password)

        try:
            # Check for urgent emails
            urgent = gmail.search_emails("subject:urgent")
            if urgent:
                logger.info(f"⚠️ Found {len(urgent)} urgent emails")

                # Send notification
                async with WhatsAppPlaywright(headless=True) as wa:
                    await wa.send_message(
                        "Me",
                        f"⚠️ You have {len(urgent)} urgent emails to review"
                    )

            # Archive old emails
            all_emails = gmail.read_emails("INBOX", limit=100)
            if len(all_emails) > 50:
                old_ids = [e['id'] for e in all_emails[:-50]]
                gmail.archive_email(old_ids)
                logger.info(f"📦 Archived {len(old_ids)} old emails")

        finally:
            gmail.close()

    async def schedule_daily_tasks(self):
        """Run all daily tasks"""
        logger.info("🚀 Starting daily automation...")

        # Send morning messages
        await self.send_morning_message()

        # Process emails
        await self.process_emails()

        logger.info("✅ Daily automation completed!")

async def main():
    orchestrator = DailyOrchestrator()
    await orchestrator.schedule_daily_tasks()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
```

---

## ⏰ Scheduling with `schedule` Library

```python
import schedule
import time
from daily_orchestrator import DailyOrchestrator
import asyncio

orch = DailyOrchestrator()

# Schedule tasks
schedule.every().day.at("08:00").do(
    lambda: asyncio.run(orch.send_morning_message())
)

schedule.every().day.at("09:00").do(
    lambda: asyncio.run(orch.process_emails())
)

schedule.every().hour.do(
    lambda: asyncio.run(orch.send_morning_message())
)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🚀 Deployment (PM2)

```bash
# Create PM2 config
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "zoya-linkedin",
      script: "python -m src.automations.linkedin_playwright",
      env: {
        LINKEDIN_EMAIL: process.env.LINKEDIN_EMAIL,
        LINKEDIN_PASSWORD: process.env.LINKEDIN_PASSWORD
      }
    },
    {
      name: "zoya-whatsapp",
      script: "python -m src.automations.whatsapp_playwright",
      env: {}
    },
    {
      name: "zoya-gmail",
      script: "python -m src.automations.daily_orchestrator",
      env: {
        GMAIL_EMAIL: process.env.GMAIL_EMAIL,
        GMAIL_APP_PASSWORD: process.env.GMAIL_APP_PASSWORD
      }
    }
  ]
};
EOF

# Start services
pm2 start ecosystem.config.js

# Monitor
pm2 monit
pm2 logs
```

---

## ✅ Error Handling

```python
try:
    async with LinkedInPlaywright(...) as li:
        success = await li.post_update("message")
        if not success:
            logger.error("Failed to post")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    # Cleanup happens automatically
    pass
```

---

## 📊 Status Indicators

Log levels used:

| Symbol | Level | Meaning |
|--------|-------|---------|
| ✅ | INFO | Operation succeeded |
| ⚠️ | WARNING | Partial success or minor issue |
| ❌ | ERROR | Operation failed |
| ℹ️ | INFO | Information/status |
| 📧 | INFO | Email operation |
| 💬 | INFO | Message/chat operation |
| 📌 | INFO | LinkedIn operation |

---

**API Version**: 1.0.0
**Last Updated**: 2026-03-07
**Status**: ✅ Production Ready
