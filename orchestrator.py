"""
WhatsApp Watcher Orchestrator

Coordinates the WhatsApp watcher and handles logging:
- Starts WhatsApp Watcher in a background thread
- Monitors /Needs_Action folder for new action files
- Logs all activity in JSON format
- Provides simple menu interface
"""

import json
import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
import os

from whatsapp_watcher import WhatsAppWatcher


class ActionFileMonitor:
    """Monitor /Needs_Action folder for new files."""

    def __init__(self, vault_path: str, logger: logging.Logger):
        """
        Initialize the action file monitor.

        Args:
            vault_path: Path to Obsidian vault
            logger: Logger instance
        """
        self.vault_path = Path(vault_path)
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.logger = logger
        self.seen_files = set()

    def scan(self) -> None:
        """Scan for new action files and log them."""
        try:
            if not self.needs_action_path.exists():
                return

            for filepath in self.needs_action_path.glob("*.md"):
                if filepath.name not in self.seen_files:
                    self.seen_files.add(filepath.name)
                    self._log_action_file(filepath)

        except Exception as e:
            self.logger.error(f"Error scanning action files: {e}")

    def _log_action_file(self, filepath: Path) -> None:
        """
        Log details of a new action file.

        Args:
            filepath: Path to the action file
        """
        try:
            content = filepath.read_text(encoding='utf-8')

            # Parse YAML frontmatter
            metadata = {}
            if content.startswith('---'):
                _, frontmatter, _ = content.split('---', 2)
                for line in frontmatter.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()

            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action_type": "action_file_detected",
                "actor": "orchestrator",
                "target": metadata.get('from', 'unknown'),
                "parameters": {
                    "filename": filepath.name,
                    "priority": metadata.get('priority', 'normal'),
                    "type": metadata.get('type', 'unknown'),
                    "status": metadata.get('status', 'unknown')
                },
                "result": "logged"
            }

            self.logger.info(json.dumps(log_entry))

        except Exception as e:
            self.logger.error(f"Error parsing action file: {e}")


class OrchestratorLogger:
    """JSON logger for orchestrator events."""

    def __init__(self, vault_path: str):
        """
        Initialize the JSON logger.

        Args:
            vault_path: Path to vault (for logs folder)
        """
        self.vault_path = Path(vault_path)
        self.logs_path = self.vault_path / "Logs"
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Get today's log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.logs_path / f"{today}.json"

        # Setup logger
        self.logger = logging.getLogger("orchestrator")
        self.logger.setLevel(logging.INFO)

        # File handler with JSON formatter
        handler = logging.FileHandler(self.log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

        # Console handler for visibility
        console = logging.StreamHandler()
        console.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        )
        self.logger.addHandler(console)

    def log_event(self, action_type: str, actor: str, target: str = "",
                  parameters: dict = None, result: str = "success") -> None:
        """
        Log an event in JSON format.

        Args:
            action_type: Type of action (e.g., 'whatsapp_message_detected')
            actor: Who performed the action (e.g., 'whatsapp_watcher')
            target: Target of the action (e.g., sender name)
            parameters: Additional parameters
            result: Result status (e.g., 'success', 'error', 'pending')
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "parameters": parameters or {},
            "result": result
        }
        self.logger.info(json.dumps(log_entry))


class Orchestrator:
    """
    Master orchestrator for WhatsApp Watcher system.

    Manages:
    - WhatsApp Watcher thread
    - Action file monitoring
    - JSON logging
    - User interface menu
    """

    def __init__(self):
        """Initialize orchestrator from .env configuration."""
        load_dotenv()

        self.vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./AI_Employee_Vault")
        self.session_path = os.getenv("WHATSAPP_WATCHER_SESSION_PATH", "./whatsapp_session")
        self.keywords_str = os.getenv("WHATSAPP_WATCHER_KEYWORDS", "urgent,asap,invoice,payment")
        self.check_interval = int(os.getenv("WHATSAPP_WATCHER_CHECK_INTERVAL", "30"))
        self.browser_headless = os.getenv("WHATSAPP_WATCHER_BROWSER_HEADLESS", "true").lower() == "true"
        self.browser_timeout = int(os.getenv("WHATSAPP_WATCHER_BROWSER_TIMEOUT", "60"))
        self.log_level = os.getenv("WHATSAPP_WATCHER_LOG_LEVEL", "INFO")
        self.dry_run = os.getenv("WHATSAPP_WATCHER_DRY_RUN", "false").lower() == "true"

        # Parse keywords
        self.keywords = [k.strip() for k in self.keywords_str.split(",")]

        # Setup logging
        self.json_logger = OrchestratorLogger(self.vault_path)
        self.logger = self.json_logger.logger

        # Initialize components
        self.watcher: Optional[WhatsAppWatcher] = None
        self.watcher_thread: Optional[threading.Thread] = None
        self.monitor = ActionFileMonitor(self.vault_path, self.logger)
        self.running = False

        self.logger.info(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "action_type": "orchestrator_started",
            "actor": "orchestrator",
            "target": "",
            "parameters": {
                "vault_path": str(self.vault_path),
                "session_path": str(self.session_path),
                "keywords": self.keywords,
                "check_interval": self.check_interval,
                "dry_run": self.dry_run
            },
            "result": "initialized"
        }))

    def start_watcher(self) -> None:
        """Start WhatsApp Watcher in background thread."""
        if self.watcher_thread is not None and self.watcher_thread.is_alive():
            print("⚠ Watcher already running")
            return

        try:
            print("\n[*] Starting WhatsApp Watcher...")

            self.watcher = WhatsAppWatcher(
                vault_path=self.vault_path,
                session_path=self.session_path,
                keywords=self.keywords,
                check_interval=self.check_interval,
                browser_headless=self.browser_headless,
                browser_timeout=self.browser_timeout,
                log_level=self.log_level,
                dry_run=self.dry_run
            )

            self.watcher_thread = threading.Thread(
                target=self.watcher.run,
                daemon=True
            )
            self.watcher_thread.start()

            self.running = True

            self.logger.info(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "action_type": "watcher_started",
                "actor": "orchestrator",
                "target": "whatsapp_watcher",
                "parameters": {"thread_id": self.watcher_thread.ident},
                "result": "success"
            }))

            print("✓ WhatsApp Watcher started (running in background)")
            print(f"  Check interval: {self.check_interval}s")
            print(f"  Watching keywords: {', '.join(self.keywords)}")
            print()

        except Exception as e:
            print(f"✗ Error starting watcher: {e}")
            self.logger.error(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "action_type": "watcher_error",
                "actor": "orchestrator",
                "target": "whatsapp_watcher",
                "parameters": {"error": str(e)},
                "result": "error"
            }))

    def stop_watcher(self) -> None:
        """Stop WhatsApp Watcher."""
        if self.watcher is None or not self.watcher_thread.is_alive():
            return

        try:
            print("\n[*] Stopping WhatsApp Watcher...")
            self.watcher.stop()
            self.watcher_thread.join(timeout=5)
            self.running = False

            self.logger.info(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "action_type": "watcher_stopped",
                "actor": "orchestrator",
                "target": "whatsapp_watcher",
                "parameters": {},
                "result": "success"
            }))

            print("✓ Watcher stopped")
            print()

        except Exception as e:
            print(f"✗ Error stopping watcher: {e}")

    def list_pending_actions(self) -> None:
        """List all pending action files."""
        needs_action_path = Path(self.vault_path) / "Needs_Action"

        if not needs_action_path.exists():
            print("\n⚠ Needs_Action folder not found")
            return

        action_files = list(needs_action_path.glob("*.md"))

        if not action_files:
            print("\n✓ No pending actions")
            return

        print(f"\n📋 Pending Actions ({len(action_files)}):")
        print("-" * 70)

        for filepath in sorted(action_files):
            try:
                content = filepath.read_text(encoding='utf-8')

                # Parse metadata
                metadata = {}
                if content.startswith('---'):
                    _, frontmatter, _ = content.split('---', 2)
                    for line in frontmatter.strip().split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()

                # Print file info
                priority = metadata.get('priority', 'normal')
                from_name = metadata.get('from', 'unknown')
                received = metadata.get('received', 'unknown')

                print(f"  {filepath.name}")
                print(f"    From: {from_name}")
                print(f"    Priority: {priority}")
                print(f"    Received: {received}")
                print()

            except Exception as e:
                print(f"  {filepath.name} (error reading: {e})")

        print("-" * 70)

    def show_menu(self) -> None:
        """Display interactive menu."""
        while True:
            print("\n" + "=" * 70)
            print("WhatsApp Watcher Orchestrator")
            print("=" * 70)
            print()

            if self.running:
                print("Status: ✓ RUNNING")
            else:
                print("Status: ✗ STOPPED")

            print()
            print("Commands:")
            print("  [S] Start watcher")
            print("  [T] Stop watcher")
            print("  [L] List pending actions")
            print("  [Q] Quit")
            print()

            choice = input("Enter command: ").strip().upper()

            if choice == "S":
                self.start_watcher()
            elif choice == "T":
                self.stop_watcher()
            elif choice == "L":
                self.list_pending_actions()
            elif choice == "Q":
                print("\nExiting...")
                self.stop_watcher()
                break
            else:
                print("⚠ Invalid command")

    def run_continuous(self) -> None:
        """Run orchestrator continuously (for use with PM2)."""
        self.start_watcher()

        try:
            while True:
                # Scan for new action files
                self.monitor.scan()
                time.sleep(5)

        except KeyboardInterrupt:
            print("\n\nShutting down...")
            self.stop_watcher()


def main():
    """Main entry point."""
    import sys

    # Check if running with --daemon flag (for PM2)
    if "--daemon" in sys.argv:
        print("Starting WhatsApp Watcher in daemon mode...")
        orchestrator = Orchestrator()
        orchestrator.run_continuous()
    else:
        # Interactive menu mode
        orchestrator = Orchestrator()
        orchestrator.show_menu()


if __name__ == "__main__":
    main()
