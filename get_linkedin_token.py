#!/usr/bin/env python3
"""Get LinkedIn OAuth Access Token — Interactive Browser-based Flow

Usage:
    python3 get_linkedin_token.py

This will:
    1. Open your browser to LinkedIn login
    2. Redirect back with authorization code
    3. Exchange code for access token
    4. Extract your Person URN
    5. Print .env values to add
"""

import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
from pathlib import Path
from dotenv import load_dotenv, set_key

import requests

# Load existing .env
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")

if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
    print("❌ LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET not set in .env")
    print("   Add them manually from https://www.linkedin.com/developers/apps")
    exit(1)

REDIRECT_URI = "http://localhost:9999/callback"
SCOPES = ["openid", "profile", "w_member_social"]


class LinkedInCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth redirect from LinkedIn"""

    auth_code = None
    error = None

    def do_GET(self):
        """Handle GET request from LinkedIn redirect"""
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)

        if "code" in params:
            LinkedInCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h1>Success!</h1><p>You can close this window and return to terminal.</p>"
            )
        elif "error" in params:
            LinkedInCallbackHandler.error = params.get("error_description", ["Unknown error"])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<h1>❌ Error: {LinkedInCallbackHandler.error}</h1>".encode()
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>No authorization code received</h1>")

    def log_message(self, *args, **kwargs):
        """Suppress default logging"""
        pass


def get_access_token():
    """Step 1: Get authorization code, Step 2: Exchange for access token"""

    print("\n" + "="*70)
    print("🔐 LinkedIn OAuth Token Generator")
    print("="*70)

    # Step 1: Generate auth URL
    auth_params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "zoya_linkedin_auth_2025",
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(auth_params)}"

    print("\n📱 Opening browser for LinkedIn login...")
    print("   If it doesn't open, visit this URL:")
    print(f"   {auth_url}\n")

    # Start local server
    server = HTTPServer(("localhost", 9999), LinkedInCallbackHandler)
    print("⏳ Waiting for callback... (listening on localhost:9999)")

    # Open browser
    webbrowser.open(auth_url)

    # Wait for callback
    while LinkedInCallbackHandler.auth_code is None and LinkedInCallbackHandler.error is None:
        server.handle_request()

    server.server_close()

    if LinkedInCallbackHandler.error:
        print(f"\n❌ Auth failed: {LinkedInCallbackHandler.error}")
        return None

    auth_code = LinkedInCallbackHandler.auth_code
    print(f"✅ Got authorization code: {auth_code[:20]}...")

    # Step 2: Exchange code for token
    print("\n🔄 Exchanging code for access token...")
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    }

    try:
        response = requests.post(token_url, data=token_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Token exchange failed: {response.text}")
            return None

        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 0)

        print(f"✅ Got access token (expires in {expires_in // 3600} hours)")
        return access_token

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def get_person_urn(access_token):
    """Get your LinkedIn Person URN"""
    print("\n🔍 Getting your Person URN...")

    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        response = requests.get("https://api.linkedin.com/v2/me", headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"⚠️  Could not fetch person URN: {response.text}")
            return None

        person_id = response.json().get("id")
        person_urn = f"urn:li:person:{person_id}"

        print(f"✅ Your Person URN: {person_urn}")
        return person_urn

    except Exception as e:
        print(f"⚠️  Error getting Person URN: {e}")
        return None


def save_to_env(access_token, person_urn):
    """Save credentials to .env"""
    env_path = PROJECT_ROOT / ".env"

    print("\n💾 Saving to .env...")

    updates = {
        "LINKEDIN_CLIENT_ID": LINKEDIN_CLIENT_ID,
        "LINKEDIN_CLIENT_SECRET": LINKEDIN_CLIENT_SECRET,
        "LINKEDIN_ACCESS_TOKEN": access_token,
    }

    if person_urn:
        updates["LINKEDIN_PERSON_URN"] = person_urn

    updates["LINKEDIN_DRY_RUN"] = "false"

    for key, value in updates.items():
        set_key(env_path, key, value)
        print(f"   {key}={'*' * 10}...")

    print(f"✅ Saved to {env_path}")


def main():
    """Main flow"""
    # Get token
    access_token = get_access_token()
    if not access_token:
        return

    # Get Person URN
    person_urn = get_person_urn(access_token)

    # Save to .env
    save_to_env(access_token, person_urn)

    print("\n" + "="*70)
    print("✅ SETUP COMPLETE!")
    print("="*70)
    print("\nYour LinkedIn account is ready for posting!")
    print("\nNext steps:")
    print("  1. Test: python3 src/linkedin_poster.py")
    print("  2. Create posts in AI_Employee_Vault/Pending_Approval/")
    print("  3. Move to Approved/ to publish\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
