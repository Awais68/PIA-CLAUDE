#!/usr/bin/env python3
"""
Gmail OAuth Token Generator
Creates token.json from credentials.json
"""

import os
import sys
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

PROJECT_ROOT = Path(__file__).resolve().parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    print("\n" + "="*70)
    print("📧 Gmail OAuth Token Generator")
    print("="*70)
    
    # Check credentials.json exists
    if not CREDENTIALS_FILE.exists():
        print(f"\n❌ credentials.json not found at: {CREDENTIALS_FILE}")
        return False
    
    print(f"\n✅ Found credentials.json")
    
    # Create OAuth flow
    print("\n⏳ Starting OAuth flow...")
    print("   (A browser window will open for Gmail authorization)")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES,
            redirect_uri='http://localhost'
        )
        
        # Run the local server for OAuth
        print("\n📱 Opening browser for Gmail authorization...")
        creds = flow.run_local_server(port=0)
        
        # Save the token
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print(f"\n✅ SUCCESS! token.json created!")
        print(f"   Location: {TOKEN_FILE}")
        
        # Verify token works
        print("\n" + "="*70)
        print("✅ Verifying Gmail Access")
        print("="*70)
        
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        print("\n✅ Gmail token is valid and working!")
        print(f"\n📧 Gmail is ready to use with Zoya!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
