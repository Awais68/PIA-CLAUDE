"""
Base Watcher Abstract Class

Provides common functionality for all watchers (WhatsApp, Email, etc.):
- Vault path setup and validation
- Check interval loop with error handling
- Logging with timestamps
- Abstract methods for subclasses to implement
"""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Any, List


class BaseWatcher(ABC):
    """
    Abstract base class for monitoring external services and creating action files.

    Subclasses must implement:
    - check_for_updates(): Returns list of updates to process
    - create_action_file(): Creates markdown file in Needs_Action folder
    """

    def __init__(
        self,
        vault_path: str,
        check_interval: int = 30,
        log_level: str = "INFO"
    ):
        """
        Initialize the base watcher.

        Args:
            vault_path: Path to the Obsidian vault (string or Path)
            check_interval: Seconds between checks (default: 30)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.vault_path = Path(vault_path).resolve()
        self.needs_action_path = self.vault_path / "Needs_Action"
        self.check_interval = check_interval
        self.running = False

        # Setup logging
        self.logger = self._setup_logger(log_level)

        # Validate vault structure
        self._validate_vault_structure()

    def _setup_logger(self, log_level: str) -> logging.Logger:
        """
        Setup logger with timestamp formatting.

        Args:
            log_level: Logging level as string

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Console handler with timestamp
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _validate_vault_structure(self) -> None:
        """
        Validate that vault path exists and has required folders.

        Raises:
            FileNotFoundError: If vault path doesn't exist
            NotADirectoryError: If vault path is not a directory
        """
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path does not exist: {self.vault_path}")

        if not self.vault_path.is_dir():
            raise NotADirectoryError(f"Vault path is not a directory: {self.vault_path}")

        # Ensure Needs_Action directory exists
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Vault validated at: {self.vault_path}")

    @abstractmethod
    def check_for_updates(self) -> List[Any]:
        """
        Check for new updates (messages, emails, etc.).

        Subclasses must implement this method.

        Returns:
            List of updates found. Format depends on subclass implementation.
        """
        pass

    @abstractmethod
    def create_action_file(self, update: Any) -> None:
        """
        Create a markdown action file from an update.

        Subclasses must implement this method to format updates as markdown
        files in the Needs_Action folder.

        Args:
            update: Update object from check_for_updates()
        """
        pass

    def run(self) -> None:
        """
        Main loop: continuously check for updates and create action files.

        Runs indefinitely until interrupted (Ctrl+C). Catches all errors
        and logs them without crashing.
        """
        self.running = True
        self.logger.info(f"Starting {self.__class__.__name__} (interval: {self.check_interval}s)")

        try:
            while self.running:
                try:
                    # Check for updates
                    updates = self.check_for_updates()

                    if updates:
                        self.logger.info(f"Found {len(updates)} update(s)")
                        for update in updates:
                            try:
                                self.create_action_file(update)
                            except Exception as e:
                                self.logger.error(f"Error creating action file: {e}", exc_info=True)

                    # Wait before next check
                    time.sleep(self.check_interval)

                except KeyboardInterrupt:
                    self.logger.info("Received interrupt signal, stopping...")
                    break
                except Exception as e:
                    self.logger.error(f"Error in check loop: {e}", exc_info=True)
                    # Wait before retrying to avoid rapid loop on repeated errors
                    time.sleep(self.check_interval)

        finally:
            self.running = False
            self.logger.info(f"Stopped {self.__class__.__name__}")

    def stop(self) -> None:
        """Stop the watcher loop."""
        self.running = False
        self.logger.info("Stop signal sent")
