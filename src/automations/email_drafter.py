"""Email Draft Skill - TF-IDF based smart email drafting using past emails."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from anthropic import Anthropic

from src.config import DONE, PENDING_APPROVAL, INBOX
from src.utils import log_action

logger = logging.getLogger(__name__)

class EmailDrafter:
    """TF-IDF based email draft generation from past emails."""

    def __init__(self):
        """Initialize email drafter."""
        self.client = Anthropic()
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        self.past_emails = []
        self.tfidf_matrix = None
        self._load_past_emails()

    def _load_past_emails(self) -> None:
        """Load all emails from Done/ folder for TF-IDF training."""
        if not DONE.exists():
            return

        for email_file in DONE.glob("*.md"):
            try:
                content = email_file.read_text()
                # Extract email body (skip frontmatter)
                body = self._extract_body(content)
                if body:
                    self.past_emails.append({
                        "file": email_file.name,
                        "body": body,
                        "content": content
                    })
            except Exception as e:
                logger.warning(f"Failed to load email {email_file.name}: {e}")

        if self.past_emails:
            bodies = [e["body"] for e in self.past_emails]
            self.tfidf_matrix = self.vectorizer.fit_transform(bodies)
            logger.info(f"Loaded {len(self.past_emails)} past emails for TF-IDF training")

    def _extract_body(self, content: str) -> str:
        """Extract email body from markdown (skip frontmatter and metadata)."""
        # Skip frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        # Extract text after "## Body" or "## Message"
        for section in ["## Body", "## Message", "## Content"]:
            if section in content:
                body = content.split(section, 1)[1]
                # Remove markdown formatting
                body = re.sub(r'\n+', ' ', body)
                body = re.sub(r'[#*_`\[\]]', '', body)
                return body.strip()

        # Fallback: return entire content
        return re.sub(r'\n+', ' ', content).strip()

    def find_similar_emails(self, subject: str, context: str = "", top_k: int = 3) -> list[dict]:
        """Find top-k similar past emails using TF-IDF cosine similarity.

        Args:
            subject: Email subject
            context: Additional context about the email
            top_k: Number of similar emails to return

        Returns:
            List of similar emails with similarity scores
        """
        if self.tfidf_matrix is None or len(self.past_emails) == 0:
            return []

        query = f"{subject} {context}"
        query_vec = self.vectorizer.transform([query])

        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]

        similar = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Minimum similarity threshold
                similar.append({
                    "file": self.past_emails[idx]["file"],
                    "similarity": float(similarities[idx]),
                    "body": self.past_emails[idx]["body"][:200],  # Preview
                    "content": self.past_emails[idx]["content"]
                })

        return similar

    def draft_reply(self, incoming_email: dict) -> dict:
        """Draft a reply to an incoming email using Claude and TF-IDF context.

        Args:
            incoming_email: Dict with keys: subject, sender, body, context

        Returns:
            Dict with keys: subject, body, similar_emails
        """
        subject = incoming_email.get("subject", "")
        body = incoming_email.get("body", "")
        sender = incoming_email.get("sender", "")
        context = incoming_email.get("context", "")

        # Find similar past emails
        similar = self.find_similar_emails(subject, body, top_k=3)

        # Build Claude prompt
        similar_context = ""
        if similar:
            similar_context = "\n\nHere are similar past email replies for reference:\n"
            for i, sim in enumerate(similar, 1):
                similar_context += f"\n--- Similar Email {i} (similarity: {sim['similarity']:.2f}) ---\n"
                similar_context += f"{sim['body']}\n"

        prompt = f"""Draft a professional email reply to this incoming email:

**From**: {sender}
**Subject**: {subject}
**Body**: {body}

{similar_context}

**Additional Context**: {context}

Draft a concise, professional reply email that:
1. Addresses the sender's main points
2. Maintains a professional tone (inspired by similar past emails)
3. Is 2-3 paragraphs max
4. Includes a closing signature

Respond with ONLY the email body text, no subject line or metadata."""

        try:
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            draft_body = message.content[0].text.strip()

            return {
                "subject": f"Re: {subject}",
                "body": draft_body,
                "similar_emails": similar,
                "sender": sender
            }

        except Exception as e:
            logger.error(f"Failed to generate email draft: {e}")
            return {
                "subject": f"Re: {subject}",
                "body": "Unable to generate draft. Please compose manually.",
                "similar_emails": similar,
                "error": str(e)
            }

    def save_draft(self, draft: dict) -> str:
        """Save email draft to Pending_Approval/ folder.

        Args:
            draft: Draft dict from draft_reply()

        Returns:
            Path to saved draft file
        """
        PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")

        draft_file = PENDING_APPROVAL / f"EMAIL_DRAFT_{now}.md"

        # Build markdown content
        similar_refs = ""
        if draft.get("similar_emails"):
            similar_refs = "\n\n## Similar Past Emails\n\n"
            for sim in draft["similar_emails"]:
                similar_refs += f"- {sim['file']} (similarity: {sim['similarity']:.2f})\n"

        content = f"""---
type: email_draft
approval_required: true
source: tfidf_drafter
created: {datetime.now().isoformat()}
sender: {draft.get('sender', 'unknown')}
---

# Email Draft

**To**: {draft.get('sender', 'unknown')}
**Subject**: {draft.get('subject', 'Re: ...')}

## Body

{draft.get('body', '')}

---

## Draft Metadata

**Generated**: {datetime.now().isoformat()}
**Source**: TF-IDF Email Drafter
**Approval Required**: Yes

{similar_refs}
"""

        draft_file.write_text(content)
        log_action("email_drafter", f"Saved draft to {draft_file.name}", result="success")
        return str(draft_file)

    def process_incoming_email(self, email_file: str) -> None:
        """Process an incoming email from Inbox/ and create draft in Pending_Approval/.

        Args:
            email_file: Path to email file in Inbox/
        """
        path = Path(email_file)
        if not path.exists():
            logger.error(f"Email file not found: {email_file}")
            return

        try:
            content = path.read_text()

            # Parse email metadata
            email = self._parse_email_file(content)

            # Generate draft
            draft = self.draft_reply(email)

            # Save draft
            self.save_draft(draft)

        except Exception as e:
            logger.error(f"Failed to process email {email_file}: {e}")

    def _parse_email_file(self, content: str) -> dict:
        """Parse email file from markdown format."""
        email = {
            "subject": "Unknown",
            "sender": "Unknown",
            "body": "",
            "context": ""
        }

        # Extract frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    frontmatter = parts[1]
                    # Simple key-value parsing
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if key == "subject":
                                email["subject"] = value
                            elif key == "from" or key == "sender":
                                email["sender"] = value
                except Exception:
                    pass
                content = parts[2]

        # Extract body section
        if "## Body" in content:
            email["body"] = content.split("## Body", 1)[1].strip()
        elif "## Message" in content:
            email["body"] = content.split("## Message", 1)[1].strip()
        else:
            email["body"] = content

        return email


def main():
    """CLI entry point for email drafter."""
    import sys

    drafter = EmailDrafter()

    if len(sys.argv) < 2:
        print("Usage: zoya-email-draft [draft|process|test]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "draft" and len(sys.argv) > 2:
        email_file = sys.argv[2]
        drafter.process_incoming_email(email_file)
        print(f"Draft created for {email_file}")

    elif cmd == "test":
        # Test with sample email
        test_email = {
            "subject": "Project Update Request",
            "sender": "manager@company.com",
            "body": "Can you provide an update on the current project status?",
            "context": "Q1 planning review"
        }
        draft = drafter.draft_reply(test_email)
        print("Generated Draft:")
        print(f"Subject: {draft['subject']}")
        print(f"Body:\n{draft['body']}")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
