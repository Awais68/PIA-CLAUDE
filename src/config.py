"""Central configuration for Zoya."""

from pathlib import Path

# Resolve project root (parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

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

# Watcher settings
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md"}
FILE_STABILITY_WAIT = 2  # seconds to wait for file to finish writing
FILE_STABILITY_CHECKS = 3  # number of stable size checks before accepting
MAX_FILE_SIZE_MB = 10
WATCHER_POLL_INTERVAL = 1  # seconds between watchdog polls

# Orchestrator settings
ORCHESTRATOR_POLL_INTERVAL = 5  # seconds between queue checks
MAX_BATCH_SIZE = 10  # max files to process per Claude invocation
MAX_RETRIES = 3  # retries before quarantine

# Lock file
ORCHESTRATOR_LOCK = PROJECT_ROOT / "orchestrator.lock.pid"
