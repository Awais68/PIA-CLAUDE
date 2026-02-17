# LinkedIn Poster Skill

## Purpose
Draft LinkedIn posts based on processed documents, achievements, or
scheduled content. All posts require HITL approval before publishing.

## When This Skill Is Used
When the orchestrator processes a file with `action: linkedin_post` in its
frontmatter, or when a scheduled briefing triggers a LinkedIn update.

## Input
- Metadata file with content to post about
- Company_Handbook.md for brand voice and LinkedIn guidelines
- Previous posts in /Done/ for tone consistency

## Processing Steps
1. Read the source content
2. Draft a LinkedIn post following Company_Handbook.md brand voice
3. Keep post under 1300 characters (LinkedIn optimal length)
4. Include relevant hashtags (3-5 max)
5. Set `approval_required: true` — all social posts need human review
6. Write draft to Pending_Approval/

## Output Format
Create a post file in Pending_Approval/:
```markdown
---
type: linkedin_post
source_ref: <original file queued_name>
created_at: <ISO timestamp>
approval_required: true
status: pending_approval
platform: linkedin
---

## Draft Post
<LinkedIn post content here>

## Hashtags
#tag1 #tag2 #tag3

## Notes for Reviewer
- <any context about why this post was drafted>
- <suggested posting time if applicable>
```

## Special Rules
- ALL LinkedIn posts MUST go through HITL approval — never auto-publish
- Follow Company_Handbook.md tone guidelines strictly
- No controversial topics, politics, or unverified claims
- Include a call-to-action when appropriate
- Tag relevant company page if applicable
