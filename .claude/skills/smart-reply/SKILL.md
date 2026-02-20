---
skill_name: SmartReply
version: 1.0
trigger: "Automatic — called by orchestrator after every gmail email is processed"
inputs: Processed email metadata .md file (source: gmail), Contacts/, Company_Handbook.md
outputs: REPLY_*.md in /Pending_Approval/ for high-priority/VIP emails; nothing for low-priority
approval_required: "YES — always. REPLY_*.md requires human move to /Approved/ before sending"
max_runtime: 2
---

## Objective

Automatically draft professional email replies for high-priority or VIP-client
emails, routing every draft through HITL approval before any email is sent.
Eliminates manual drafting for routine client communication while keeping the
human firmly in control of all outbound messages.

## Decision Logic

```
Email arrives (source: gmail)
         │
         ▼
Is sender in Contacts/ OR Company_Handbook.md?  ──YES──► VIP = true
         │
         ▼
Does subject/body contain high-priority keywords?
(urgent, invoice, payment, meeting, complaint, deadline, asap, quote...)
         │
         ▼
VIP=true OR keyword_hit=true?
   │                │
  YES               NO
   │                │
   ▼                ▼
Draft reply    Low priority — file to Done/, no draft
   │
   ▼
Save REPLY_*.md to /Pending_Approval/
(NEVER auto-send)
```

## Priority Keyword Reference

**Subject keywords:** urgent, asap, invoice, payment, overdue, past due, meeting,
complaint, problem, issue, deadline, quote, proposal, contract, immediately, escalate

**Body keywords:** urgent, asap, immediately, invoice, payment due, overdue,
please respond, awaiting your reply, outstanding balance, final reminder, legal action,
complaint, not working, broken, failed, wrong amount, meeting tomorrow

## Step-by-Step Process

1. **Orchestrator calls** `process_email_for_smart_reply(meta_path)` after Done/ move

2. **Load known emails** from:
   - `AI_Employee_Vault/Contacts/CONTACT_*.md` (identity: field containing @)
   - `AI_Employee_Vault/Company_Handbook.md` (all email-shaped strings)

3. **Classify email** — returns `(should_draft, priority, reason)`

4. **If low priority** → log `smart_reply_skipped`, return None

5. **If should draft:**
   - Load tone/style from `Company_Handbook.md` (## Tone or ## Communication Style section)
   - Call Claude: `generate_reply_with_claude(from, subject, body, tone, priority)`
   - Claude generates 2-4 paragraph professional reply (output only — no auto-commit rules)

6. **Write approval file** `Pending_Approval/REPLY_<timestamp>_<subject>.md`:
   ```yaml
   type: email_reply_draft
   original_email_id: <gmail_id>
   to: sender@example.com
   subject: Re: Original Subject
   priority: high|medium
   draft_reason: VIP client / high-priority keyword
   suggested_by: claude
   status: pending_approval
   approval_required: true
   action: send_email
   ```

7. **Human reviews** the draft in Obsidian:
   - ✅ Approve: move to `/Approved/` → orchestrator sends via Gmail MCP
   - ✏️ Edit: edit body in Obsidian before moving to `/Approved/`
   - ❌ Reject: move to `/Rejected/` → discarded

8. **Orchestrator picks up** `REPLY_*.md` from Approved/ and calls `process_approved_replies()`

## .env Variables

```
SMART_REPLY_ENABLED=true      # false disables feature entirely
SMART_REPLY_DRY_RUN=true      # true = log only, don't write REPLY_*.md files
```

## Success Criteria

- VIP / high-priority emails get `REPLY_*.md` in Pending_Approval/ within one orchestrator cycle
- `suggested_by: claude` in frontmatter
- Low-priority emails produce no REPLY file
- No email is ever sent without a human explicitly moving to /Approved/
- Audit log entry `smart_reply_drafted` for every draft created

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Claude unavailable | Use fallback draft template, still write REPLY_*.md |
| Company_Handbook.md missing | Use default tone: "Professional, polite, concise" |
| Contacts/ empty | Treat all senders as non-VIP; still check keywords |
| Email body not found | Extract from raw .md content, skip if still empty |
| SMART_REPLY_ENABLED=false | Return None immediately, no processing |

## Testing

```bash
# Test on a specific email metadata file
uv run python -m src.automations.smart_reply AI_Employee_Vault/Done/EMAIL_*.md --dry-run

# Verify a REPLY_*.md was created in Pending_Approval/
ls AI_Employee_Vault/Pending_Approval/REPLY_*
```

## Example REPLY_*.md

```markdown
---
type: email_reply_draft
original_email_id: 18a7b3c4d5e6f789
to: client@acme-corp.com
subject: Re: Invoice #1042 - Payment Overdue
priority: HIGH
draft_reason: VIP client (client@acme-corp.com) + priority keyword
suggested_by: claude
status: pending_approval
approval_required: true
---

# Email Reply Draft

**To:** client@acme-corp.com
**Subject:** Re: Invoice #1042 - Payment Overdue
**Priority:** HIGH
**Reason:** VIP client + high-priority keyword

---

## Drafted Reply

Thank you for reaching out regarding Invoice #1042.

I sincerely apologise for any inconvenience the delay has caused. I have reviewed
our records and can confirm the payment is being processed immediately. You should
expect to see the funds cleared within 2-3 business days.

Please don't hesitate to contact me if you have any further questions.

Best regards,
[Your Name]

---

Move to `/Approved/` to send · Move to `/Rejected/` to discard
```
