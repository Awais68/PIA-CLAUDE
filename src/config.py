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


def validate_config() -> list[str]:
    """Return a list of config warnings/errors. Empty list = all OK."""
    issues = []
    # Check vault folders exist
    for folder in [INBOX, NEEDS_ACTION, IN_PROGRESS, DONE, QUARANTINE, LOGS,
                   PLANS, APPROVED, REJECTED, BRIEFINGS, PENDING_APPROVAL]:
        if not folder.is_dir():
            issues.append(f"Missing vault folder: {folder.name}")

    # Check AI provider config
    if AI_PROVIDER == "qwen" and not DASHSCOPE_API_KEY:
        issues.append("AI_PROVIDER=qwen but DASHSCOPE_API_KEY is empty")
    if AI_PROVIDER == "gmail" and not GOOGLE_CLIENT_ID:
        issues.append("Gmail configured but GOOGLE_CLIENT_ID is empty")

    return issues
