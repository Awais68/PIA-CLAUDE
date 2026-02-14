# Gmail Processor Skill

## Purpose
Process email files ingested from Gmail. Analyze the email content,
determine urgency, extract action items, and categorize.

## When This Skill Is Used
When the orchestrator invokes Claude to process a file with `source: gmail` in its frontmatter.

## Input
- Markdown file in /Needs_Action/ with `source: gmail` frontmatter
- Contains email headers (from, to, subject, date), body text, and attachment references
- Company_Handbook.md for business rules and known contacts

## Processing Steps
1. Read the email markdown file
2. Analyze sender — is this a known contact from Company_Handbook.md or new?
3. Determine urgency based on:
   - Subject line keywords: urgent, asap, invoice, payment, deadline, overdue
   - Sender importance (from Company_Handbook.md known contacts list)
   - Content analysis (sentiment, action required)
4. Extract action items:
   - Reply needed? (question asked, request made)
   - Payment required? (invoice attached, amount mentioned)
   - Meeting request? (date/time mentioned)
   - Follow-up needed? (deadline mentioned)
5. If email has attachments, note them in action items with filenames
6. Categorize the email:
   - `client_email` — from a known client, business-related
   - `invoice` — contains or is about an invoice/payment
   - `newsletter` — marketing content, no action needed
   - `notification` — automated service notification
   - `personal` — non-business communication
   - `spam` — unsolicited, low value
7. Assign priority:
   - `high` — client email requiring action, invoice, payment reference
   - `medium` — requires response but not urgent
   - `low` — informational only (newsletters, notifications)
8. Write results to metadata file using standard inbox-processor output format
9. If action requires sending a reply or making a payment: set `approval_required: true`

## Output Format
Update the existing frontmatter with:
```yaml
type: <email category from step 6>
priority: <high|medium|low>
source: gmail
status: done
processed_at: <ISO timestamp>
approval_required: <true|false>
approval_reason: <reason if approval needed>
```

Add sections:
```markdown
## Summary
<2-3 sentence summary of the email>

## Action Items
- [ ] <extracted action 1>
- [ ] <extracted action 2>

## Category
<why this categorization was chosen>
```

## Special Rules
- NEVER auto-reply to emails — all replies must go through HITL approval
- Flag any email mentioning money amounts > $500 as high priority
- Flag emails with attachments named "invoice" or "contract" as high priority
- Newsletters and notifications should be priority: low
- If the email is clearly spam, set priority: low and note in summary
