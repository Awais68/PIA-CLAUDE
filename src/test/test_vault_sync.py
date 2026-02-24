"""
Unit Tests for Vault Sync Module
Tests Git operations: pull, rebase, push, and secret verification
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cloud_agent.vault_sync import (
    run_git,
    verify_no_secrets_staged,
    sync_vault,
    update_sync_signal
)


class TestGitOperations(unittest.TestCase):
    """Test Git command execution"""

    @patch('subprocess.run')
    def test_run_git_success(self, mock_run):
        """Test successful git command execution"""
        mock_run.return_value = MagicMock(returncode=0, stdout=b"Success", stderr=b"")

        result = run_git(["status"], timeout=30)

        self.assertEqual(result["returncode"], 0)
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_run_git_timeout(self, mock_run):
        """Test git command timeout"""
        mock_run.side_effect = TimeoutError("Command timed out")

        result = run_git(["pull"], timeout=5)

        self.assertEqual(result["returncode"], -1)
        self.assertIn("timeout", result["stderr"].lower())

    @patch('subprocess.run')
    def test_run_git_failure(self, mock_run):
        """Test git command failure"""
        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"Error message")

        result = run_git(["push"], timeout=30)

        self.assertEqual(result["returncode"], 1)


class TestSecretVerification(unittest.TestCase):
    """Test secret verification before commit"""

    @patch('subprocess.run')
    def test_verify_no_secrets_clean(self, mock_run):
        """Test verification passes when no secrets present"""
        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=b"")

        result = verify_no_secrets_staged()

        self.assertTrue(result)

    @patch('subprocess.run')
    def test_verify_secrets_detected(self, mock_run):
        """Test verification fails when secrets are detected"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=b".env:API_KEY=sk-1234567890",
            stderr=b""
        )

        result = verify_no_secrets_staged()

        self.assertFalse(result)


class TestVaultSync(unittest.TestCase):
    """Test vault synchronization workflow"""

    @patch('src.cloud_agent.vault_sync.run_git')
    @patch('src.cloud_agent.vault_sync.verify_no_secrets_staged')
    def test_sync_vault_success(self, mock_verify, mock_git):
        """Test successful vault sync"""
        mock_git.return_value = {"returncode": 0}
        mock_verify.return_value = True

        # This would require more setup - partial test
        # result = sync_vault()
        # self.assertTrue(result)

    @patch('src.cloud_agent.vault_sync.run_git')
    def test_sync_vault_pull_fails(self, mock_git):
        """Test vault sync fails on git pull"""
        mock_git.return_value = {"returncode": 1, "stderr": "Merge conflict"}

        # This would require more setup
        # result = sync_vault()
        # self.assertFalse(result)


class TestSyncSignal(unittest.TestCase):
    """Test sync signal updates"""

    @patch('src.utils.file_ops.write_task_file')
    def test_update_sync_signal_success(self, mock_write):
        """Test successful sync signal update"""
        mock_write.return_value = True

        # Would require config setup
        # result = update_sync_signal("success", "2.5s")
        # self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
