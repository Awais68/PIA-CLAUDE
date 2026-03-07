#!/usr/bin/env python3
"""
Zoya Full Workflow Test
Tests all integrated APIs working together
"""

import sys
from pathlib import Path
import smtplib
import requests
from requests_oauthlib import OAuth1

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_gmail():
    """Test Gmail"""
    print("\n" + "="*70)
    print("📧 TEST 1: Gmail (Email)")
    print("="*70)
    
    email = "codetheagent1@gmail.com"
    password = "ovas erml jsot ybhk"
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email, password)
        print("✅ Gmail authenticated")
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Gmail failed: {e}")
        return False

def test_twitter():
    """Test Twitter"""
    print("\n" + "="*70)
    print("🐦 TEST 2: Twitter")
    print("="*70)
    
    api_key = "kVEQNBz8HQTvw1ys8RjjHoKC3"
    api_secret = "JYxbTKaPZJyWXhS4OcSY6PyRSmSxm8xHNy0W2IshsmdEijRtvu"
    access_token = "2024933692812959744-6i5ZiHXJPdl2JrIJ9a6hNNMmgSr8CR"
    access_token_secret = "meIcGCC6wfVL7e0mG9BEJMTLmRkQp9R6yCgVYOFOK8lRl"
    
    try:
        auth = OAuth1(api_key, api_secret, access_token, access_token_secret)
        url = "https://api.twitter.com/1.1/account/verify_credentials.json"
        response = requests.get(url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Twitter authenticated: @{data['screen_name']}")
            return True
        else:
            print(f"❌ Twitter failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Twitter failed: {e}")
        return False

def test_linkedin():
    """Test LinkedIn"""
    print("\n" + "="*70)
    print("💼 TEST 3: LinkedIn")
    print("="*70)
    
    access_token = "AQUHbu8XcCiFKNwhktO_dNIwC7yGCeDfC4DuAC4XB7N27jP0BdDWxuZhQ0NUwa7-YVCvQj8zVxOhNqss8TSJqHFeEEEcIxT88rH4BqC0D8mhsQdrSOKOH_y8YEZFYfccF1DxAlp-3o3D3eCQHOMoO0CgsmRMV6eNYViq__RHcxvxWNfRoFr7tNjLzJpqCpHW7PQi7BuvYWFQN57CefmLt4fgwnFUsUHfSsm6K3RevyvJE5hEySpVM2Kb8NJzzxq7sKoAFkj5lpFS5Di9fVDsCbtR-5pA-IQQkqI4aWOwqPjSUiz90OReJeGAI2Kj7V8Axhn-5vaXUGsT8k7Kk-kMY4suayT31w"
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ LinkedIn authenticated: {data.get('name', 'User')}")
            return True
        else:
            print(f"❌ LinkedIn failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LinkedIn failed: {e}")
        return False

def test_facebook():
    """Test Facebook"""
    print("\n" + "="*70)
    print("📘 TEST 4: Facebook")
    print("="*70)
    
    page_id = "122101733007271133"
    page_token = "EAAa47R551fkBQZCLGJzZAtuJElZAbNYo8ghhXHIaBpZAqEmPiJk7HGX31Td1QR5DPZCFOBkKJ4RGidoAIYfuvEMyxQIkiKXcf0VZB9NzZBSpjWVJTZCTfejnv1g5PKOXCkZAZBcPslAUQtyxmgYvgG92upcX2rr5Nixmi2VyuXbl1MTIEgpPebNpdjckyZAUf9N9XhHfvg3WV5xcfzdppGElxmel7tkLPCBbwgu6xVkRRyehx37QvDXM6nhUNy09XjwEcwPlMVtl3PAzvBLQTJOyo5KlLmQ"
    
    try:
        url = f"https://graph.facebook.com/v18.0/{page_id}"
        params = {"fields": "name,id", "access_token": page_token}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Facebook authenticated: {data.get('name')}")
            return True
        else:
            print(f"❌ Facebook failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Facebook failed: {e}")
        return False

def test_whatsapp():
    """Test WhatsApp (local session check)"""
    print("\n" + "="*70)
    print("💬 TEST 5: WhatsApp (Local Session)")
    print("="*70)
    
    session_path = Path.home() / "whatsapp_session" / "state.json"
    
    if session_path.exists():
        print(f"✅ WhatsApp session found: {session_path}")
        return True
    else:
        print(f"⚠️  WhatsApp session not created yet")
        print(f"   Run: ./.venv/bin/python ~/whatsapp_login.py")
        return False

def main():
    print("\n" + "█"*70)
    print("█ ZOYA FULL WORKFLOW TEST")
    print("█ Testing all integrated APIs")
    print("█"*70)
    
    results = {
        "Gmail": test_gmail(),
        "Twitter": test_twitter(),
        "LinkedIn": test_linkedin(),
        "Facebook": test_facebook(),
        "WhatsApp": test_whatsapp(),
    }
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for api, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {api}")
    
    print(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n" + "█"*70)
        print("█ 🎉 ALL TESTS PASSED!")
        print("█ Zoya is fully operational and ready for production!")
        print("█"*70)
        return 0
    else:
        print("\n❌ Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
