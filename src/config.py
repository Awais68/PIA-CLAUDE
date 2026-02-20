"""Central configuration for Zoya."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve project root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Vault paths
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
INBOX = VAULT_PATH / "Inbox"
NEEDS_ACTION = VAULT_PATH / "Needs_Action"
IN_PROGRESS = VAULT_PATH / "In_Progress"
DONE = VAULT_PATH / "Done"
QUARANTINE = VAULT_PATH / "Quarantine"
LOGS = VAULT_PATH / "Logs"
DASHBOARD = VAULT_PATH / "Dashboard.md"
HANDBOOK = VAULT_PATH / "Company_Handbook.md"

# Silver tier folders
PLANS = VAULT_PATH / "Plans"
APPROVED = VAULT_PATH / "Approved"
REJECTED = VAULT_PATH / "Rejected"
BRIEFINGS = VAULT_PATH / "Briefings"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"

# Gold tier folders
CONTACTS = VAULT_PATH / "Contacts"
BUSINESS_TASKS = VAULT_PATH / "Business" / "Tasks"
CLIENTS = VAULT_PATH / "Clients"

# Bank watcher paths
BANK_INBOX   = VAULT_PATH / "Inbox" / "Bank"
BANK_ARCHIVE = VAULT_PATH / "Archive" / "Bank"

# Watcher settings
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md"}
FILE_STABILITY_WAIT = 2  # seconds to wait for file to finish writing
FILE_STABILITY_CHECKS = 3  # number of stable size checks before accepting
MAX_FILE_SIZE_MB = 10
WATCHER_POLL_INTERVAL = 1  # seconds between watchdog polls

# Orchestrator settings
ORCHESTRATOR_POLL_INTERVAL = 30  # seconds between queue checks
MAX_BATCH_SIZE = 10  # max files to process per Claude invocation
MAX_RETRIES = 3  # retries before quarantine

# Lock file
ORCHESTRATOR_LOCK = PROJECT_ROOT / "orchestrator.lock.pid"

# AI Provider: "claude", "qwen", or "ollama"
AI_PROVIDER = os.getenv("AI_PROVIDER", "claude")

# Ollama (local, free)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Qwen via DashScope (OpenAI-compatible endpoint)
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# Gmail settings
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")
GMAIL_POLL_INTERVAL = int(os.getenv("GMAIL_POLL_INTERVAL", "60"))  # seconds
GMAIL_MAX_RESULTS = int(os.getenv("GMAIL_MAX_RESULTS", "10"))
GMAIL_CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
GMAIL_TOKEN_FILE = PROJECT_ROOT / "token.json"

# LinkedIn settings
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PAGE_ID = os.getenv("LINKEDIN_PAGE_ID", "")
LINKEDIN_DRY_RUN = os.getenv("LINKEDIN_DRY_RUN", "true").lower() == "true"

# WhatsApp Business API (Meta Cloud API)
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "zoya_verify_token")
WHATSAPP_WEBHOOK_PORT = int(os.getenv("WHATSAPP_PORT", "5001"))

# Twitter / X API v2 (OAuth 1.0a)
# .env may use access_Token / ACCESS_TOKEN_SECRET (non-standard names)
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN") or os.getenv("access_Token", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET") or os.getenv("ACCESS_TOKEN_SECRET", "")
TWITTER_DRY_RUN = os.getenv("TWITTER_DRY_RUN", "true").lower() == "true"

# Odoo Community settings
# .env may use ODOO_USER and ODOO_API_KEY (non-standard names)
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USERNAME = os.getenv("ODOO_USERNAME") or os.getenv("ODOO_USER", "admin")
ODOO_API_KEY = os.getenv("ODOO_API_KEY", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD") or ODOO_API_KEY or "admin"


def validate_config() -> list[str]:
    """Return a list of config warnings/errors. Empty list = all OK."""
    issues = []
    # Check vault folders exist
    for folder in [INBOX, NEEDS_ACTION, IN_PROGRESS, DONE, QUARANTINE, LOGS,
                   PLANS, APPROVED, REJECTED, BRIEFINGS, PENDING_APPROVAL, CONTACTS,
                   BUSINESS_TASKS, CLIENTS]:
        if not folder.is_dir():
            issues.append(f"Missing vault folder: {folder.name}")

    # Check AI provider config
    if AI_PROVIDER == "qwen" and not DASHSCOPE_API_KEY:
        issues.append("AI_PROVIDER=qwen but DASHSCOPE_API_KEY is empty")

    # Platform credential checks (non-fatal warnings)
    if not GOOGLE_CLIENT_ID:
        issues.append("Gmail: GOOGLE_CLIENT_ID not set — Gmail watcher will not authenticate")
    if not WHATSAPP_ACCESS_TOKEN:
        issues.append("WhatsApp: WHATSAPP_ACCESS_TOKEN not set — media downloads disabled")
    if not LINKEDIN_ACCESS_TOKEN and not LINKEDIN_DRY_RUN:
        issues.append("LinkedIn: LINKEDIN_ACCESS_TOKEN not set but DRY_RUN is off")
    if not TWITTER_API_KEY and not TWITTER_DRY_RUN:
        issues.append("Twitter: TWITTER_API_KEY not set but TWITTER_DRY_RUN is off")

    return issues
