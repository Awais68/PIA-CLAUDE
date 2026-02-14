# Pending Approval — Human-in-the-Loop (HITL) Workflow

## What Is This Folder?

This folder contains items that require **human review and approval** before Zoya can take action. Files appear here when:

- An invoice exceeds $500
- A contract has a deadline within 7 days
- An outbound email needs to be sent
- A LinkedIn post is ready to publish
- A WhatsApp reply is drafted
- Any file deletion is requested

## How to Approve or Reject

### Option A: Drag and Drop in Obsidian
1. Open Obsidian and navigate to this folder
2. Review the file contents (summary, action items, approval reason)
3. **To Approve:** Drag the file to the `/Approved/` folder
4. **To Reject:** Drag the file to the `/Rejected/` folder

### Option B: Move via Terminal
```bash
# To approve:
mv AI_Employee_Vault/Pending_Approval/FILE_NAME.md AI_Employee_Vault/Approved/

# To reject:
mv AI_Employee_Vault/Pending_Approval/FILE_NAME.md AI_Employee_Vault/Rejected/
```

## What Happens After Your Decision

- **Approved items:** The orchestrator picks them up on its next cycle, executes the pending action (send email, post to LinkedIn, etc.), and moves the file to `/Done/` with `approved_by: human`.
- **Rejected items:** The orchestrator moves them to `/Done/` with `status: rejected`. No action is taken.

## File Format

Each pending approval file contains:

```yaml
---
type: <document type>
status: pending_approval
approval_required: true
approval_reason: <why this needs your review>
approval_requested_at: <timestamp>
---

## Summary
<what this item is about>

## Action Items
<what Zoya wants to do>

## To Approve
Move this file to /Approved/

## To Reject
Move this file to /Rejected/
```

## Approval Rules

These thresholds are defined in `Company_Handbook.md`:

| Trigger | Threshold | Why |
|---------|-----------|-----|
| Invoice amount | > $500 | Financial risk |
| Contract deadline | < 7 days | Time-sensitive decision |
| Outbound email | All | Prevent unauthorized communication |
| LinkedIn post | All | Brand/reputation protection |
| WhatsApp reply | All | Prevent unauthorized communication |
| File deletion | All | Data loss prevention |

## Important Notes

- Files left in this folder indefinitely will NOT be processed
- The orchestrator checks this folder, `/Approved/`, and `/Rejected/` every cycle (5 seconds)
- You can edit the file contents before approving (e.g., modify an email draft)
- All approval/rejection decisions are logged in `Logs/` for audit trail
