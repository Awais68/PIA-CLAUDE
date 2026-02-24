"""
Email Simulation Tool
Creates fake email tasks for testing the email processing pipeline
"""

from datetime import datetime
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import VaultPaths
from src.utils.file_ops import write_task_file


def create_fake_email_task(
    from_email: str = "john.doe@example.com",
    subject: str = "Meeting Request",
    body: str = "Hi, I wanted to discuss the Q1 strategy for the upcoming project. Would you be available next Tuesday at 2 PM?"
) -> bool:
    """
    Create a fake email task for testing

    Args:
        from_email: Sender email
        subject: Email subject
        body: Email body

    Returns:
        True if task created successfully
    """
    try:
        metadata = {
            "type": "email",
            "from": from_email,
            "subject": subject,
            "created": datetime.utcnow().isoformat(),
            "source": "test_simulation"
        }

        content = f"""From: {from_email}
Subject: {subject}

{body}
"""

        task_path = VaultPaths.NEEDS_ACTION / f"EMAIL_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

        success = write_task_file(task_path, metadata, content)

        if success:
            print(f"✅ Created test email task: {task_path.name}")
            print(f"   From: {from_email}")
            print(f"   Subject: {subject}")
            return True
        else:
            print(f"❌ Failed to create task at {task_path}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def create_multiple_test_emails(count: int = 3) -> int:
    """
    Create multiple test email tasks

    Args:
        count: Number of test emails to create

    Returns:
        Number of successfully created tasks
    """
    test_emails = [
        {
            "from": "alice@example.com",
            "subject": "Project Update",
            "body": "The frontend redesign is 80% complete. Expected to finish by end of week. Any concerns?"
        },
        {
            "from": "bob@example.com",
            "subject": "Budget Review",
            "body": "Need your approval on Q2 budget allocation. The detailed breakdown is attached. Please review and confirm."
        },
        {
            "from": "charlie@example.com",
            "subject": "Customer Inquiry",
            "body": "Customer is asking about integrations with Salesforce. Can we support this? What would be the timeline?"
        },
        {
            "from": "diana@example.com",
            "subject": "Team Feedback",
            "body": "Team meeting recap: everyone appreciated the new async meeting format. Should we continue this approach?"
        },
        {
            "from": "eve@example.com",
            "subject": "Technical Issue",
            "body": "API endpoint returning 500 errors in production. Users unable to complete payments. This is critical."
        }
    ]

    created_count = 0
    for i in range(min(count, len(test_emails))):
        email = test_emails[i]
        if create_fake_email_task(email["from"], email["subject"], email["body"]):
            created_count += 1

    return created_count


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create test email tasks")
    parser.add_argument("--count", type=int, default=1, help="Number of test emails to create")
    parser.add_argument("--from", dest="from_email", default="test@example.com", help="Sender email")
    parser.add_argument("--subject", default="Test Email", help="Email subject")
    parser.add_argument("--body", default="This is a test email body.", help="Email body")

    args = parser.parse_args()

    if args.count > 1:
        print(f"\n📧 Creating {args.count} test email tasks...")
        created = create_multiple_test_emails(args.count)
        print(f"\n✅ Created {created}/{args.count} test email tasks\n")
    else:
        print(f"\n📧 Creating test email task...")
        if create_fake_email_task(args.from_email, args.subject, args.body):
            print("✅ Test email task created successfully\n")
        else:
            print("❌ Failed to create test email task\n")
