# HITL Evaluator Skill

## Purpose
Evaluate whether a task or action requires Human-In-The-Loop (HITL) approval
before proceeding. Route approved/rejected items to the correct vault folders.

## When This Skill Is Used
When the orchestrator encounters a file with `approval_required: true` in its
frontmatter, or when a Plan.md has `requires_approval: true`.

## Input
- Metadata file or Plan.md with `approval_required: true`
- Company_Handbook.md for approval thresholds and rules

## Processing Steps
1. Read the item requiring approval
2. Determine the approval category:
   - `financial` — involves money, payments, purchases
   - `communication` — external emails, messages, posts
   - `data` — modifying or deleting records
   - `operational` — scheduling, process changes
3. Check Company_Handbook.md for auto-approve rules
4. If auto-approvable, move to Approved/ with reason
5. If requires human review, move to Pending_Approval/ and notify
6. Log the decision in the metadata frontmatter

## Output Format
Update frontmatter:
```yaml
approval_status: <pending|approved|rejected>
approval_category: <financial|communication|data|operational>
approval_reason: <why approval is needed or was auto-granted>
evaluated_at: <ISO timestamp>
```

## Special Rules
- NEVER auto-approve financial actions over $100
- NEVER auto-approve external communications to clients
- Low-priority newsletters/notifications can be auto-approved
- Log all approval decisions for audit trail
- If rejected, move file to Rejected/ with rejection reason
