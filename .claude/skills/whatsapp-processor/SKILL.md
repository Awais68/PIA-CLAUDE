# WhatsApp Processor Skill

## Purpose
Process incoming WhatsApp messages ingested via the WhatsApp Business API
webhook. Analyze message content, determine intent, and categorize.

## When This Skill Is Used
When the orchestrator processes a file with `source: whatsapp` in its frontmatter.

## Input
- Markdown file in /Needs_Action/ with `source: whatsapp` frontmatter
- Contains: sender number, message text, media references (if any)
- Company_Handbook.md for business rules and known contacts

## Processing Steps
1. Read the WhatsApp message markdown file
2. Identify sender — known contact from Company_Handbook.md or new?
3. Determine message intent:
   - `inquiry` — asking a question about products/services
   - `order` — placing or modifying an order
   - `complaint` — reporting an issue
   - `follow_up` — referencing a previous conversation
   - `general` — casual or unclassified message
4. Extract key information (dates, amounts, product names)
5. Assign priority based on sender and intent
6. Write results to metadata file

## Output Format
Update frontmatter:
```yaml
type: <message intent from step 3>
priority: <high|medium|low>
source: whatsapp
sender: <phone number>
status: done
processed_at: <ISO timestamp>
approval_required: <true|false>
```

Add sections:
```markdown
## Summary
<1-2 sentence summary of the message>

## Action Items
- [ ] <extracted action>

## Suggested Reply
<draft reply if applicable — requires HITL approval to send>
```

## Special Rules
- NEVER auto-reply to WhatsApp messages — all replies require HITL approval
- Messages mentioning payments or orders are always high priority
- Media messages (images, documents) should note the media type
- Group messages should be flagged for human review
