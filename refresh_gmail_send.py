#!/usr/bin/env python3
"""
Refresh Gmail token with SEND scope
"""

import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail send scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    project_root = Path(__file__).parent
    credentials_file = project_root / "credentials.json"
    token_file = project_root / "token.json"
    
    if not credentials_file.exists():
        print("❌ credentials.json not found!")
        return
    
    print("🔐 Re-authenticating with Gmail SEND scope...")
    print("A browser window will open. Please authenticate.")
    
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_file), SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save new token
    token_file.write_text(creds.to_json())
    print(f"✅ Token saved to {token_file}")
    print(f"📋 Scopes: {creds.scopes}")
    
if __name__ == '__main__':
    main()
