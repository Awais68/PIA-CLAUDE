"""Content Generator — AI-powered LinkedIn post generation.

Uses the configured AI provider to generate professional LinkedIn posts
based on business context, recent activity, or specified topics.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from src.config import (
    AI_PROVIDER,
    DASHSCOPE_API_KEY,
    DONE,
    HANDBOOK,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    PENDING_APPROVAL,
    QWEN_BASE_URL,
    QWEN_MODEL,
)
from src.utils import setup_logger

logger = setup_logger("content_generator")

# Post templates for different content types
TEMPLATES = {
    "product_announcement": (
        "Write a LinkedIn post announcing a new product or feature. "
        "Tone: professional, enthusiastic. Include a call-to-action. "
        "Length: 150-250 words. End with 3-5 relevant hashtags."
    ),
    "industry_insight": (
        "Write a LinkedIn post sharing an industry insight or trend. "
        "Tone: thought-leader, informative. Ask a question to drive engagement. "
        "Length: 150-250 words. End with 3-5 relevant hashtags."
    ),
    "customer_success": (
        "Write a LinkedIn post about a customer success story. "
        "Tone: celebratory, professional. Focus on results and impact. "
        "Length: 150-250 words. End with 3-5 relevant hashtags."
    ),
    "behind_the_scenes": (
        "Write a LinkedIn post showing behind-the-scenes of our work. "
        "Tone: authentic, relatable. Humanize the brand. "
        "Length: 100-200 words. End with 3-5 relevant hashtags."
    ),
    "general": (
        "Write a professional LinkedIn post about the given topic. "
        "Tone: professional, engaging. Include a call-to-action. "
        "Length: 150-250 words. End with 3-5 relevant hashtags."
    ),
}


def _load_business_context() -> str:
    """Load business context from Company_Handbook.md if available."""
    if HANDBOOK.exists():
        try:
            return HANDBOOK.read_text(encoding="utf-8")[:2000]
        except Exception:
            pass
    return "Zoya — Personal AI Employee for business automation."


def _get_recent_activity() -> str:
    """Summarize recent Done items for content inspiration."""
    if not DONE.exists():
        return ""
    done_files = sorted(DONE.glob("FILE_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    if not done_files:
        return ""
    summaries = []
    for f in done_files:
        try:
            text = f.read_text(encoding="utf-8")
            # Extract original_name from frontmatter
            match = re.search(r"original_name:\s*(.+)", text)
            if match:
                summaries.append(match.group(1).strip())
        except Exception:
            pass
    return "Recent activity: " + ", ".join(summaries) if summaries else ""


def generate_post(
    topic: str,
    post_type: str = "general",
    context: str = "",
) -> str:
    """Generate a LinkedIn post using the configured AI provider.

    Args:
        topic: What the post is about.
        post_type: One of: product_announcement, industry_insight,
                   customer_success, behind_the_scenes, general.
        context: Additional context to include.

    Returns:
        Generated post text (or template fallback if AI unavailable).
    """
    template = TEMPLATES.get(post_type, TEMPLATES["general"])
    business_context = _load_business_context()
    activity = _get_recent_activity()

    prompt = (
        f"{template}\n\n"
        f"Topic: {topic}\n\n"
        f"Business context:\n{business_context[:500]}\n\n"
    )
    if context:
        prompt += f"Additional context:\n{context}\n\n"
    if activity:
        prompt += f"{activity}\n\n"

    prompt += "Write ONLY the post text followed by hashtags. No extra commentary."

    # Try AI generation
    try:
        if AI_PROVIDER in ("ollama", "qwen"):
            return _generate_with_openai_compat(prompt)
        else:
            return _generate_fallback(topic, post_type)
    except Exception:
        logger.warning("AI generation failed, using fallback template")
        return _generate_fallback(topic, post_type)


def _generate_with_openai_compat(prompt: str) -> str:
    """Generate using OpenAI-compatible API (Ollama or Qwen)."""
    from openai import OpenAI

    if AI_PROVIDER == "ollama":
        client = OpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL)
        model = OLLAMA_MODEL
    else:
        client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=QWEN_BASE_URL)
        model = QWEN_MODEL

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a professional LinkedIn content writer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )
    text = response.choices[0].message.content
    # Strip thinking tags from some models
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return text[:1300]  # LinkedIn optimal length


def _generate_fallback(topic: str, post_type: str) -> str:
    """Generate a template-based post when AI is unavailable."""
    now = datetime.now(timezone.utc).strftime("%B %Y")
    return (
        f"{topic}\n\n"
        f"We're excited to share this update with our network. "
        f"Stay tuned for more developments as we continue to innovate "
        f"and deliver value to our community.\n\n"
        f"What are your thoughts? Let us know in the comments below.\n\n"
        f"#business #innovation #growth"
    )[:1300]


def create_post_draft(
    topic: str,
    post_type: str = "general",
    context: str = "",
    source_ref: str = "",
) -> Path:
    """Generate a post and save it as an approval request.

    Args:
        topic: Post topic.
        post_type: Type of post template to use.
        context: Additional context.
        source_ref: Reference to source document.

    Returns:
        Path to the created approval file.
    """
    from src.linkedin_poster import create_approval_request

    post_content = generate_post(topic, post_type, context)

    # Extract hashtags from post (last line starting with #)
    lines = post_content.strip().split("\n")
    hashtags = ""
    for line in reversed(lines):
        if line.strip().startswith("#"):
            hashtags = line.strip()
            break

    return create_approval_request(post_content, hashtags, source_ref)
