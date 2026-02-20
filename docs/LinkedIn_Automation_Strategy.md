# LinkedIn Automation Strategy

## Approach: Official API with DRY_RUN

### Why Official API
- No risk of account suspension
- Compliant with LinkedIn ToS
- Requires company page access + app review
- `w_member_social` scope needed

### Why NOT Browser Automation
- Violates LinkedIn ToS
- High risk of account suspension
- Detection evasion is a losing game
- Unreliable (UI changes break scripts)

## Current Implementation

### DRY_RUN Mode (Default)
- `LINKEDIN_DRY_RUN=true` in `.env`
- Content is generated and routed through HITL
- Posts are logged but NOT published
- Allows demo of full workflow without API access

### Production Mode
When LinkedIn API access is approved:
1. Set `LINKEDIN_DRY_RUN=false` in `.env`
2. Set `LINKEDIN_ACCESS_TOKEN` to a valid token
3. Set `LINKEDIN_PAGE_ID` to your company page URN
4. Posts will be published via the UGC API after HITL approval

## Safety Measures
- ALL posts require HITL approval (no auto-publish)
- Content generated from Company_Handbook.md guidelines
- Max 1300 characters per post (LinkedIn optimal)
- 3-5 hashtags per post
- No controversial content, unverified claims, or confidential data

## Content Generation Pipeline
1. Topic/trigger received (manual, scheduled, or from processed document)
2. AI generates draft using business context
3. Draft saved to `Pending_Approval/LINKEDIN_*.md`
4. Human reviews in Obsidian
5. Move to `Approved/` → published (or `Rejected/` → archived)
