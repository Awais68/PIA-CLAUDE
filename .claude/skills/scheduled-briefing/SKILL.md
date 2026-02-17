# Scheduled Briefing Skill

## Purpose
Generate periodic briefing documents summarizing recent activity, pending
tasks, and upcoming deadlines. Supports daily and weekly schedules.

## When This Skill Is Used
Triggered by cron schedule or manual request. Generates a briefing
document in AI_Employee_Vault/Briefings/.

## Input
- Files in Done/ (recent activity)
- Files in Needs_Action/ (pending work)
- Files in Quarantine/ (items needing attention)
- Files in Pending_Approval/ (awaiting human review)
- Dashboard.md for current stats

## Processing Steps
1. Scan all vault folders for current state
2. Collect items processed in the briefing period (daily: last 24h, weekly: last 7d)
3. Identify pending items requiring attention
4. Summarize quarantined items needing review
5. List upcoming deadlines from action items
6. Generate the briefing document

## Output Format
Create a briefing file in Briefings/:
```markdown
---
type: briefing
period: <daily|weekly>
generated_at: <ISO timestamp>
covers_from: <start ISO timestamp>
covers_to: <end ISO timestamp>
---

# <Daily|Weekly> Briefing — <date>

## Summary
- **Processed:** <count> items
- **Pending:** <count> items
- **Quarantined:** <count> items needing review
- **Awaiting Approval:** <count> items

## Completed Items
| File | Type | Priority | Processed |
|------|------|----------|-----------|
| ... | ... | ... | ... |

## Pending Items
| File | Type | Priority | Queued |
|------|------|----------|-------|
| ... | ... | ... | ... |

## Attention Required
- <quarantined items or overdue actions>

## Upcoming Deadlines
- <extracted deadlines from action items>
```

## Special Rules
- Briefings are informational only — no actions taken
- Include counts even if zero for consistency
- Weekly briefings should include trend data if available
- Store briefings for 30 days, then archive
