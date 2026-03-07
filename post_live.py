#!/usr/bin/env python3
"""
Zoya Live Posting Script
Posts all approved content to Twitter and LinkedIn
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Set working directory
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

# Import posting functions
from src.twitter_poster import process_approved_tweets
from src.linkedin_poster import process_approved_posts as process_approved_linkedin_posts

print("\n" + "="*70)
print("🚀 ZOYA SOCIAL MEDIA POSTING — LIVE MODE ACTIVATED")
print("="*70)

print(f"\n⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"🔴 Mode: LIVE POSTING")
print(f"📍 Platforms: Twitter & LinkedIn")

print("\n" + "-"*70)
print("STEP 1: POSTING TO TWITTER")
print("-"*70)

try:
    twitter_count = process_approved_tweets()
    print(f"\n✅ Successfully processed {twitter_count} Twitter post(s)")
except Exception as e:
    print(f"❌ Twitter Error: {e}")
    import traceback
    traceback.print_exc()
    twitter_count = 0

print("\n" + "-"*70)
print("STEP 2: POSTING TO LINKEDIN")
print("-"*70)

try:
    linkedin_count = process_approved_linkedin_posts()
    print(f"\n✅ Successfully processed {linkedin_count} LinkedIn post(s)")
except Exception as e:
    print(f"❌ LinkedIn Error: {e}")
    import traceback
    traceback.print_exc()
    linkedin_count = 0

print("\n" + "="*70)
print("📊 POSTING SUMMARY")
print("="*70)
print(f"🐦 Twitter: {twitter_count} posts")
print(f"💼 LinkedIn: {linkedin_count} posts")
print(f"📈 Total: {twitter_count + linkedin_count} posts published")
print("\n✨ Posts are now live on your social media platforms!")
print("="*70 + "\n")
