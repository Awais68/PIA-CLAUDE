#!/usr/bin/env python3
"""Get LinkedIn Member ID from API"""

import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv(Path(__file__).parent / ".env")

token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()

if not token:
    print("❌ LINKEDIN_ACCESS_TOKEN not found in .env")
    exit(1)

print(f"🔍 Token loaded: {token[:20]}...")
print("\n📡 Calling LinkedIn API...")

try:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    response = requests.get("https://api.linkedin.com/v2/me", headers=headers, timeout=10)

    print(f"Status: {response.status_code}")
    print(f"Response:\n{response.text}\n")

    if response.status_code == 200:
        data = response.json()
        member_id = data.get("id")
        if member_id:
            print(f"✅ YOUR MEMBER ID: {member_id}")
            print(f"\n📋 Add to .env:")
            print(f"LINKEDIN_PERSON_URN=urn:li:member:{member_id}")
        else:
            print("⚠️  ID not found in response")
    else:
        print(f"❌ API Error: {response.status_code}")

except Exception as e:
    print(f"❌ Error: {e}")
