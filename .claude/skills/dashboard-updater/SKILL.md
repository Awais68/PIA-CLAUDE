# Dashboard Updater Skill

## Description

Refreshes the `Dashboard.md` file in the vault root with current queue counts, recent activity, and alerts.

## Trigger

Called by the orchestrator after processing completes.

## Instructions

1. **Count files** in each vault folder (exclude `.gitkeep`):
   - `AI_Employee_Vault/Inbox/`
   - `AI_Employee_Vault/Needs_Action/`
   - `AI_Employee_Vault/In_Progress/`
   - `AI_Employee_Vault/Done/`
   - `AI_Employee_Vault/Quarantine/`

2. **Read the 10 most recently modified** `.md` files in `Done/` and extract:
   - Original filename
   - Type (category)
   - Priority
   - Processed timestamp
   - First line of summary

3. **Check Quarantine/** for any items and list them as alerts.

4. **Write** the updated dashboard to `AI_Employee_Vault/Dashboard.md` using this format:

```markdown
---
last_updated: <current ISO timestamp>
version: 0.1.0
---

# Zoya Dashboard

## System Status

| Component | Status |
|-----------|--------|
| File Watcher | <Running if watcher PID exists, else Stopped> |
| Orchestrator | Running |
| Last Processing | <timestamp of most recent Done/ file> |

## Queue Summary

| Folder | Count |
|--------|-------|
| Inbox | <count> |
| Needs Action | <count> |
| In Progress | <count> |
| Done | <count> |
| Quarantine | <count> |

## Recent Activity

| Time | File | Type | Priority |
|------|------|------|----------|
| <timestamp> | <original_name> | <type> | <priority> |

## Alerts

<List any quarantined files with reasons, or "No alerts." if empty>
```

## Important Rules

- Only overwrite `Dashboard.md` — do not touch any other files.
- If a folder is empty, show count as 0.
- Cap "Recent Activity" to the 10 most recent items.
- Set `last_updated` in frontmatter to the current UTC time.
