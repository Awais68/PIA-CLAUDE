# Scheduled Briefing Skill

## Purpose
Generate periodic CEO briefing documents summarizing activity, pending tasks,
upcoming deadlines, and system health across all channels (file drop, Gmail, WhatsApp).

## When This Skill Is Used
- Triggered daily by cron via `uv run zoya-briefing`
- Triggered weekly via `uv run zoya-briefing --weekly`
- Can be invoked manually at any time
- Also called from the scheduler (`JobScheduler`) for automated generation

## Entry Point
```
uv run zoya-briefing [--weekly]
```

## Input
- `AI_Employee_Vault/Done/` — completed items with processed_at timestamps
- `AI_Employee_Vault/Needs_Action/` — pending items
- `AI_Employee_Vault/In_Progress/` — items currently being processed
- `AI_Employee_Vault/Quarantine/` — failed items needing attention
- `AI_Employee_Vault/Pending_Approval/` — items awaiting human review
- `AI_Employee_Vault/Plans/` — active plan documents

## Processing Steps
1. Determine period: daily (last 24h) or weekly (last 7 days)
2. Scan Done/ for items processed within the period
3. Compute channel breakdown (file_drop / gmail / whatsapp)
4. Compute document type breakdown
5. Collect pending, approval, and quarantine items
6. Extract action items with deadlines from recent Done/ files
7. Compute system health score (0-100, penalized by quarantine/stuck/backlog)
8. Generate the briefing document
9. Save to `AI_Employee_Vault/Briefings/BRIEFING_YYYYMMDD_HHMMSS_<period>.md`

## Output Format
```markdown
---
type: briefing
period: <daily|weekly>
generated_at: <ISO timestamp>
covers_from: <ISO timestamp>
covers_to: <ISO timestamp>
health_score: <0-100>
---

# <Daily|Weekly> Briefing — YYYY-MM-DD

**Generated:** ...
**System Health:** <score>/100

## Summary
| Metric | Count |

## Channel Breakdown
| Channel | Processed |

## Document Types
| Type | Count |

## Completed Items
| File | Type | Channel | Priority | Approval | Processed |

## Pending Items
...

## Awaiting Human Approval
...

## ⚠️ Attention Required (if quarantine items exist)
...

## Upcoming Deadlines (if found)
...

## Weekly Trends (weekly only)
...
```

## Special Rules
- Briefings are read-only — no actions taken, no files moved
- System health score: 100 = perfect, -10 per quarantined item, -5 per stuck/pending
- Weekly briefings include 7-day trend data
- Briefings stored for 30 days, then archived
- Empty sections still shown for consistency (shows zero counts)
