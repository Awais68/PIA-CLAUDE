#!/usr/bin/env python3
"""
Zoya Multi-Platform Test Posts
Tests posting to all connected platforms
"""

import sys
import smtplib
import requests
from email.mime.text import MIMEText
from requests_oauthlib import OAuth1
from datetime import datetime

print("\n" + "█"*70)
print("█ ZOYA MULTI-PLATFORM TEST POSTS")
print("█ " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("█"*70)

# ============ TEST 1: EMAIL ============
print("\n" + "="*70)
print("📧 TEST 1: EMAIL (Gmail)")
print("="*70)

try:
    email = "codetheagent1@gmail.com"
    password = "ovas erml jsot ybhk"
    
    # Create message
    msg = MIMEText("🤖 This is a test email from Zoya AI Employee!\n\nAll systems operational ✅")
    msg['Subject'] = "[ZOYA TEST] Multi-Platform Post Test"
    msg['From'] = email
    msg['To'] = email
    
    # Send
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, password)
    server.send_message(msg)
    server.quit()
    
    print("✅ Email sent to codetheagent1@gmail.com")
except Exception as e:
    print(f"❌ Email failed: {e}")

# ============ TEST 2: TWITTER ============
print("\n" + "="*70)
print("🐦 TEST 2: TWITTER")
print("="*70)

try:
    api_key = "kVEQNBz8HQTvw1ys8RjjHoKC3"
    api_secret = "JYxbTKaPZJyWXhS4OcSY6PyRSmSxm8xHNy0W2IshsmdEijRtvu"
    access_token = "2024933692812959744-6i5ZiHXJPdl2JrIJ9a6hNNMmgSr8CR"
    access_token_secret = "meIcGCC6wfVL7e0mG9BEJMTLmRkQp9R6yCgVYOFOK8lRl"
    
    auth = OAuth1(api_key, api_secret, access_token, access_token_secret)
    
    tweet_text = "🤖 Test tweet from Zoya AI Employee! Multi-platform posting active ✅ #automation #ai"
    
    url = "https://api.twitter.com/1.1/statuses/update.json"
    params = {"status": tweet_text}
    
    response = requests.post(url, params=params, auth=auth, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Tweet posted!")
        print(f"   Text: {tweet_text[:60]}...")
        print(f"   Tweet ID: {data['id']}")
    else:
        print(f"❌ Twitter failed: {response.status_code}")
        print(f"   {response.text[:100]}")
except Exception as e:
    print(f"❌ Twitter failed: {e}")

# ============ TEST 3: LINKEDIN ============
print("\n" + "="*70)
print("💼 TEST 3: LINKEDIN")
print("="*70)

try:
    access_token = "AQUHbu8XcCiFKNwhktO_dNIwC7yGCeDfC4DuAC4XB7N27jP0BdDWxuZhQ0NUwa7-YVCvQj8zVxOhNqss8TSJqHFeEEEcIxT88rH4BqC0D8mhsQdrSOKOH_y8YEZFYfccF1DxAlp-3o3D3eCQHOMoO0CgsmRMV6eNYViq__RHcxvxWNfRoFr7tNjLzJpqCpHW7PQi7BuvYWFQN57CefmLt4fgwnFUsUHfSsm6K3RevyvJE5hEySpVM2Kb8NJzzxq7sKoAFkj5lpFS5Di9fVDsCbtR-5pA-IQQkqI4aWOwqPjSUiz90OReJeGAI2Kj7V8Axhn-5vaXUGsT8k7Kk-kMY4suayT31w"
    person_urn = "urn:li:person:JFkdUz5Dwg"
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    post_text = "🤖 Test post from Zoya AI Employee!\n\nMulti-platform automation is now live. All systems operational ✅\n\n#AI #Automation #LinkedInAPI"
    
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_text
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    url = "https://api.linkedin.com/v2/ugcPosts"
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    
    if response.status_code == 201:
        print(f"✅ LinkedIn post created!")
        print(f"   Text: {post_text[:60]}...")
    else:
        print(f"⚠️  LinkedIn: {response.status_code}")
        print(f"   Note: LinkedIn API has strict post requirements")
except Exception as e:
    print(f"❌ LinkedIn failed: {e}")

# ============ TEST 4: FACEBOOK ============
print("\n" + "="*70)
print("📘 TEST 4: FACEBOOK")
print("="*70)

try:
    page_id = "122101733007271133"
    page_token = "EAAa47R551fkBQZCLGJzZAtuJElZAbNYo8ghhXHIaBpZAqEmPiJk7HGX31Td1QR5DPZCFOBkKJ4RGidoAIYfuvEMyxQIkiKXcf0VZB9NzZBSpjWVJTZCTfejnv1g5PKOXCkZAZBcPslAUQtyxmgYvgG92upcX2rr5Nixmi2VyuXbl1MTIEgpPebNpdjckyZAUf9N9XhHfvg3WV5xcfzdppGElxmel7tkLPCBbwgu6xVkRRyehx37QvDXM6nhUNy09XjwEcwPlMVtl3PAzvBLQTJOyo5KlLmQ"
    
    post_text = "🤖 Test post from Zoya AI Employee!\n\nMulti-platform automation is now live. All systems operational ✅\n\n#AI #Automation"
    
    url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
    params = {
        "message": post_text,
        "access_token": page_token
    }
    
    response = requests.post(url, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Facebook post created!")
        print(f"   Text: {post_text[:60]}...")
        print(f"   Post ID: {data.get('id', 'N/A')}")
    else:
        print(f"❌ Facebook failed: {response.status_code}")
        print(f"   {response.json()}")
except Exception as e:
    print(f"❌ Facebook failed: {e}")

# ============ TEST 5: WHATSAPP ============
print("\n" + "="*70)
print("💬 TEST 5: WHATSAPP")
print("="*70)

try:
    session_path = "/home/awais/whatsapp_session/state.json"
    import os
    
    if os.path.exists(session_path):
        print(f"✅ WhatsApp session ready")
        print(f"   To send: Use local Playwright session")
        print(f"   Session: {session_path}")
    else:
        print(f"❌ WhatsApp session not found")
except Exception as e:
    print(f"❌ WhatsApp failed: {e}")

# ============ SUMMARY ============
print("\n" + "█"*70)
print("█ TEST COMPLETE")
print("█ Check platforms for test posts!")
print("█"*70)
