#!/usr/bin/env python3
"""Validate all API credentials and report which services are ready.

Usage: uv run python scripts/test_credentials.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    AI_PROVIDER,
    DASHSCOPE_API_KEY,
    GMAIL_CREDENTIALS_FILE,
    GMAIL_TOKEN_FILE,
    LINKEDIN_ACCESS_TOKEN,
    LINKEDIN_DRY_RUN,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    validate_config,
)


def check_ai_provider() -> tuple[str, bool]:
    """Check AI provider configuration."""
    if AI_PROVIDER == "claude":
        import shutil
        if shutil.which("claude"):
            return "AI Provider (Claude CLI)", True
        return "AI Provider (Claude CLI) — 'claude' not in PATH", False
    elif AI_PROVIDER == "ollama":
        try:
            import requests
            resp = requests.get(f"{OLLAMA_BASE_URL.replace('/v1', '')}/api/tags", timeout=5)
            models = [m["name"] for m in resp.json().get("models", [])]
            if any(OLLAMA_MODEL in m for m in models):
                return f"AI Provider (Ollama/{OLLAMA_MODEL})", True
            return f"AI Provider (Ollama) — model '{OLLAMA_MODEL}' not pulled", False
        except Exception:
            return "AI Provider (Ollama) — server not running", False
    elif AI_PROVIDER == "qwen":
        if DASHSCOPE_API_KEY and len(DASHSCOPE_API_KEY) > 5:
            return "AI Provider (Qwen/DashScope)", True
        return "AI Provider (Qwen) — DASHSCOPE_API_KEY not set", False
    return f"AI Provider ({AI_PROVIDER}) — unknown provider", False


def check_gmail() -> tuple[str, bool]:
    """Check Gmail API credentials."""
    if not GMAIL_CREDENTIALS_FILE.exists():
        return "Gmail API — credentials.json missing", False
    if GMAIL_TOKEN_FILE.exists():
        return "Gmail API (authenticated)", True
    return "Gmail API — token.json missing (run setup_gmail_auth.py)", False


def check_whatsapp() -> tuple[str, bool]:
    """Check WhatsApp API credentials."""
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    if token and phone_id and phone_id != "your_phone_number_id":
        return "WhatsApp API", True
    if token and not phone_id:
        return "WhatsApp API — WHATSAPP_PHONE_NUMBER_ID not set", False
    return "WhatsApp API — credentials not configured", False


def check_linkedin() -> tuple[str, bool]:
    """Check LinkedIn API credentials."""
    if LINKEDIN_DRY_RUN:
        return "LinkedIn API (DRY_RUN mode — no credentials needed)", True
    if LINKEDIN_ACCESS_TOKEN and len(LINKEDIN_ACCESS_TOKEN) > 10:
        return "LinkedIn API", True
    return "LinkedIn API — LINKEDIN_ACCESS_TOKEN not set", False


def check_vault() -> tuple[str, bool]:
    """Check vault folder structure."""
    issues = validate_config()
    folder_issues = [i for i in issues if "Missing vault folder" in i]
    if not folder_issues:
        return "Vault folders", True
    return f"Vault — {len(folder_issues)} folder(s) missing", False


def main() -> None:
    print("=" * 50)
    print("  Zoya Credentials & Services Check")
    print("=" * 50)
    print()

    checks = [
        check_ai_provider(),
        check_gmail(),
        check_whatsapp(),
        check_linkedin(),
        check_vault(),
    ]

    ready = 0
    for label, ok in checks:
        icon = "OK" if ok else "FAIL"
        print(f"  [{icon:>4}]  {label}")
        if ok:
            ready += 1

    print()
    print(f"  {ready}/{len(checks)} services ready")
    print("=" * 50)

    if ready < len(checks):
        print("\nTo fix missing services, see:")
        print("  - .env.example for environment variables")
        print("  - config/credentials.example.json for API setup")
        print("  - scripts/setup_gmail_auth.py for Gmail")


if __name__ == "__main__":
    main()
