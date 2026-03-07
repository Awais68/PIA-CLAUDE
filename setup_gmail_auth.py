#!/usr/bin/env python3
"""
Quick script to authenticate with Gmail using your new account.
This will open a browser window for you to authenticate.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.watchers.gmail_watcher import GmailWatcher
from src.utils import setup_logger

logger = setup_logger("gmail_auth")

if __name__ == "__main__":
    print("🔐 Starting Gmail authentication with your new account...")
    print("A browser window will open shortly. Please authenticate and authorize access.\n")

    try:
        watcher = GmailWatcher()
        watcher.setup()
        print("✅ Gmail authentication successful!")
        print("📧 Token saved. Gmail sync is now ready to use.")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)
