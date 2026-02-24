"""
Unit Tests for Claim-by-Move Protocol
Tests atomic file movement (atomicity, no double-processing)
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.file_ops import (
    claim_task,
    move_to_done,
    move_to_queue,
    read_task_file,
    write_task_file
)


class TestClaimByMove(unittest.TestCase):
    """Test atomic claim-by-move protocol"""

    def setUp(self):
        """Set up temporary directories for testing"""
        self.temp_dir = TemporaryDirectory()
        self.needs_action = Path(self.temp_dir.name) / "Needs_Action"
        self.in_progress = Path(self.temp_dir.name) / "In_Progress"
        self.done = Path(self.temp_dir.name) / "Done"
        self.queue = Path(self.temp_dir.name) / "Queue"

        # Create directories
        self.needs_action.mkdir(exist_ok=True)
        self.in_progress.mkdir(exist_ok=True)
        self.done.mkdir(exist_ok=True)
        self.queue.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up temporary directories"""
        self.temp_dir.cleanup()

    def test_claim_task_success(self):
        """Test successful task claiming"""
        # Create a test task file
        task_file = self.needs_action / "test_task.md"
        task_file.write_text("---\ntype: email\n---\nTest content")

        # Claim the task
        claimed_path = claim_task(str(task_file), str(self.in_progress / "email"))

        # Verify original file is gone
        self.assertFalse(task_file.exists())

        # Verify file exists in in_progress
        self.assertTrue(Path(claimed_path).exists())

    def test_claim_task_nonexistent(self):
        """Test claiming nonexistent task returns None"""
        nonexistent = self.needs_action / "nonexistent.md"
        claimed = claim_task(str(nonexistent), str(self.in_progress))
        self.assertIsNone(claimed)

    def test_no_double_processing(self):
        """Test that claimed task cannot be claimed twice"""
        # Create task
        task_file = self.needs_action / "task.md"
        task_file.write_text("---\ntype: email\n---\nContent")

        # First claim succeeds
        first_claim = claim_task(str(task_file), str(self.in_progress / "email"))
        self.assertIsNotNone(first_claim)

        # Second claim fails (file already gone)
        second_claim = claim_task(str(task_file), str(self.in_progress / "email"))
        self.assertIsNone(second_claim)

    def test_move_to_done(self):
        """Test moving completed task to Done folder"""
        # Create task in in_progress
        in_progress_file = self.in_progress / "email" / "test.md"
        in_progress_file.parent.mkdir(exist_ok=True)
        in_progress_file.write_text("Completed task")

        # Move to done
        done_path = self.done / "test.md"
        success = move_to_done(in_progress_file, done_path)

        self.assertTrue(success)
        self.assertFalse(in_progress_file.exists())
        self.assertTrue(done_path.exists())

    def test_move_to_queue_for_retry(self):
        """Test moving failed task to Queue for retry"""
        # Create task
        task_file = self.in_progress / "email" / "failed.md"
        task_file.parent.mkdir(exist_ok=True)
        task_file.write_text("Failed task")

        # Move to queue
        queue_path = self.queue / "email" / "failed.md"
        queue_path.parent.mkdir(exist_ok=True)
        success = move_to_queue(task_file, queue_path)

        self.assertTrue(success)
        self.assertFalse(task_file.exists())
        self.assertTrue(queue_path.exists())


class TestAtomicWrites(unittest.TestCase):
    """Test atomic file write operations"""

    def setUp(self):
        """Set up temporary directory"""
        self.temp_dir = TemporaryDirectory()
        self.test_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up"""
        self.temp_dir.cleanup()

    def test_write_task_file_creates_file(self):
        """Test that write_task_file creates file atomically"""
        task_path = self.test_path / "task.md"
        metadata = {"type": "email", "from": "test@example.com"}
        content = "Test task content"

        # Note: write_task_file expects VaultPaths, so this is a partial test
        # Real test would require proper config setup

    def test_concurrent_writes_safe(self):
        """Test that concurrent writes don't cause corruption"""
        # This would require actual concurrent execution testing
        # Placeholder for future implementation
        pass


if __name__ == "__main__":
    unittest.main()
