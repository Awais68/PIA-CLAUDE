# Twitter Agent Skill

## Purpose
Monitor Twitter/X mentions, manage tweet scheduling from a queue file, track
brand/keyword activity, and produce a weekly analytics summary. All outbound
tweets require human-in-the-loop (HITL) approval before publishing.

## When This Skill Is Used
- Triggered every 30 minutes by `TwitterWatcher` (src/watchers/twitter_watcher.py)
- Can be invoked manually: `claude "Run the twitter-agent skill"`
- Weekly analytics summary generated every Monday at 08:00

## Entry Point (manual)
```
claude "Run the twitter-agent skill to check mentions and schedule tweets"
```

## Permissions Required
- Read: `AI_Employee_Vault/Business/Tweet_Queue.md`
- Read: `AI_Employee_Vault/Needs_Action/`
- Write: `AI_Employee_Vault/Needs_Action/` (urgent mentions)
- Write: `AI_Employee_Vault/Pending_Approval/` (tweet drafts)
- Write: `AI_Employee_Vault/Briefings/` (analytics reports)

## Keyword Monitoring Configuration
Edit the lists below to match your brand context:

```yaml
brand_keywords:
  - "YourBrandName"        # Your primary brand / handle
  - "@YourHandle"          # Your Twitter username

competitor_keywords:
  - "CompetitorA"
  - "CompetitorB"

industry_keywords:
  - "AI employee"
  - "personal AI"
  - "AI automation"
  - "Claude Code"
```

---

## Step-by-Step Processing

### Phase 1 — Mention Monitoring
1. Call `tweepy.Client.search_recent_tweets()` for each brand keyword (last 30 min window)
2. For each mention received:
   - Classify urgency:
     - **High**: contains "urgent", "ASAP", "broken", "lawsuit", "refund", direct `@mention` with question
     - **Medium**: general brand mention, product feedback
     - **Low**: retweets, likes, generic praise
   - High-urgency mentions → write `TWITTER_MENTION_<timestamp>.md` to `/Needs_Action/`
   - Medium/Low → log to `AI_Employee_Vault/Logs/twitter_mentions.log`

**Needs_Action file format for urgent mention:**
```markdown
---
type: twitter_mention
source: twitter
urgency: high
tweet_id: <id>
author: @<handle>
received_at: <ISO timestamp>
status: pending
priority: high
---

## Urgent Twitter Mention

**Author:** @<handle>
**Tweet:** <full tweet text>
**URL:** https://twitter.com/<handle>/status/<id>
**Received:** <datetime>

## Why Urgent
<reason classification>

## Suggested Actions
- [ ] Review mention and draft reply
- [ ] Escalate to human if legal/PR issue
- [ ] Move to /Approved/ after human review
```

### Phase 2 — Tweet Queue Processing
1. Read `AI_Employee_Vault/Business/Tweet_Queue.md`
2. Find all unchecked items `- [ ]` in the `## Scheduled` section
3. For each scheduled tweet where the `scheduled_for` datetime ≤ now:
   - Generate final tweet text (expand placeholders if any)
   - Call `src/twitter_poster.py::create_approval_request()` to create HITL draft
   - Mark the queue item as `- [x] (sent to approval YYYY-MM-DD HH:MM)`
4. Write updated `Tweet_Queue.md` back to disk

### Phase 3 — Weekly Analytics Summary
Runs once per week (triggered by scheduler on Mondays).

Collect via Twitter API v2:
- Follower count delta (this week vs last week)
- Total impressions for your tweets
- Top 3 tweets by engagement (likes + retweets + replies)
- Mention volume by day
- Keyword trend: which monitored keywords spiked

Write report to `AI_Employee_Vault/Briefings/TWITTER_ANALYTICS_<YYYYMMDD>.md`:

```markdown
---
type: twitter_analytics
period: weekly
generated_at: <ISO timestamp>
covers_from: <start of week>
covers_to: <end of week>
---

# Twitter Weekly Analytics — Week of YYYY-MM-DD

## Follower Summary
| Metric | Value |
|--------|-------|
| Followers (end of week) | N |
| New followers | +N |

## Engagement
| Metric | Count |
|--------|-------|
| Total impressions | N |
| Total engagements | N |
| Avg. engagement rate | N% |

## Top Tweets
1. "<tweet text>" — N engagements
2. "<tweet text>" — N engagements
3. "<tweet text>" — N engagements

## Mention Volume
| Day | Mentions |
|-----|---------|
| Mon | N |
...

## Trending Keywords
- "keyword" — N mentions (▲/▼ vs last week)

## Recommendations
- [ ] <AI-generated action based on data>
```

---

## Safety Rules
- **NEVER post directly.** All outbound content goes through `create_approval_request()`.
- DRY_RUN mode (default): log tweet text without calling API.
- Respect Twitter API rate limits: max 500k tweets/month on Basic tier.
- Do not store raw tweet content in Done/ — privacy-sensitive; log IDs only.
- Credentials loaded from `.env` only — never hardcoded.

## Error Handling
| Error | Action |
|-------|--------|
| API rate limit (429) | Back off 15 min, log warning |
| Auth failure | Log critical error, skip cycle |
| Tweet_Queue.md missing | Create empty queue file, continue |
| Network timeout | Retry once after 30s, then skip cycle |

## Dependencies
```
uv add tweepy
```

## Related Components
- `src/watchers/twitter_watcher.py` — runs this skill on schedule
- `src/twitter_poster.py` — handles HITL approval + actual posting
- `src/config.py` — TWITTER_* credentials
- `AI_Employee_Vault/Business/Tweet_Queue.md` — tweet scheduling queue
- `.claude/skills/scheduled-briefing/SKILL.md` — includes Twitter analytics in CEO briefing
