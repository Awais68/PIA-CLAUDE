# Email Triage Skill

## Purpose
Deeply categorize incoming emails by priority level, type, and required action.
Produces a rich triage report so the orchestrator and user can quickly understand
what each email needs and act accordingly.

## When This Skill Is Used
When the orchestrator invokes Claude to process a metadata file in `/Needs_Action/`
that has `source: gmail` in its frontmatter and `status: pending`.

## Input
- Metadata `.md` file (written by gmail_watcher) containing email headers and body
- `AI_Employee_Vault/Contacts/email_whitelist.json` — VIP/known senders
- `AI_Employee_Vault/Contacts/email_blacklist.json` — known spam senders
- `AI_Employee_Vault/Company_Handbook.md` — business rules

## Processing Steps

### Step 1: Read the Email Metadata File
Parse the frontmatter and body from the email `.md` file. Extract:
- `from` — sender email address
- `from_name` — display name if present
- `subject` — email subject line
- `received` — timestamp the email was received
- `body` — full email body text

### Step 2: Determine Sender Trust Level
Load `AI_Employee_Vault/Contacts/email_whitelist.json` and
`AI_Employee_Vault/Contacts/email_blacklist.json`.

- If sender email or domain is in whitelist → `sender_trust: VIP` or `KNOWN`
  (use `VIP` for entries with `"tier": "vip"`, `KNOWN` for standard entries)
- If sender email or domain is in blacklist → `sender_trust: SPAM`
- Otherwise → `sender_trust: UNKNOWN`

### Step 3: Assign Priority

Evaluate the following signals in order:

**URGENT** — requires action within 1 hour:
- Subject or body contains: `urgent`, `ASAP`, `asap`, `critical`, `emergency`,
  `deadline today`, `!!!`, `[URGENT]`
- Sender trust is `VIP`
- Email mentions an expiry or deadline within 24 hours
- Subject contains explicit time pressure (e.g. "by end of day", "by EOD")

**HIGH** — requires action within 24 hours:
- Subject or body contains: `important`, `invoice`, `payment`, `contract`,
  `overdue`, `required`, `need`, `deadline this week`
- Sender trust is `KNOWN` and email requests a response or action
- Deadline mentioned within 3 days
- Financial amount > $500 referenced

**NORMAL** — requires action within 3 days:
- Standard business correspondence from unknown but legitimate senders
- Newsletters from trusted/whitelisted domains
- Regular project updates or status emails

**LOW** — process when convenient:
- Newsletters from unknown sources
- Marketing and promotional emails
- "FYI" messages with no action required
- Automated system notifications
- Sender trust is `SPAM` (downgrade to LOW and flag, do not auto-delete)

### Step 4: Classify Category

Choose exactly one:
- `ACTION` — requires a response or specific action from the user
- `FYI` — informational only; no action needed
- `NEWSLETTER` — subscription/newsletter content
- `SPAM` — promotional, unsolicited, or unwanted
- `AUTOMATED` — system-generated notifications (CI/CD, SaaS alerts, receipts)

### Step 5: Extract Key Information
- **Key points**: 2–4 bullet points summarising the main content
- **Action items**: Any explicit or implied tasks, as markdown checkboxes
- **Deadlines**: Any dates or time references mentioned
- **Requires approval**: Set `true` if the email implies spending money, sending an
  external reply, signing a document, or any other irreversible action

### Step 6: Draft a Recommended Response
Write a suggested action or reply in plain language. If no reply is needed, state
"No response required." NEVER send a reply — all outbound messages go through HITL.

### Step 7: Write the Triage Output
Overwrite the metadata file with the full output format below.
Preserve every existing frontmatter field; only add or update the new ones.

### Step 8: Log the Triage
Append one line to the current day's log file
(`AI_Employee_Vault/Logs/YYYY-MM-DD.log`):

```
[TIMESTAMP] Email triaged - Priority: <PRIORITY>, Category: <CATEGORY>, From: <SENDER_EMAIL>, Subject: <SUBJECT>
```

## Output Format

```markdown
---
type: email
source: gmail
priority: <URGENT|HIGH|NORMAL|LOW>
category: <ACTION|FYI|NEWSLETTER|SPAM|AUTOMATED>
sender: <sender@example.com>
sender_name: <Display Name or "Unknown">
sender_trust: <VIP|KNOWN|UNKNOWN|SPAM>
subject: <email subject>
received: <ISO 8601 timestamp from original email>
deadline: <ISO 8601 timestamp if a deadline was found, otherwise "none">
action_required: <true|false>
requires_approval: <true|false>
tags: [<tag1>, <tag2>]
triaged_at: <current ISO 8601 timestamp>
status: triaged
original_name: <from existing frontmatter>
queued_name: <from existing frontmatter>
queued_at: <from existing frontmatter>
retry_count: <from existing frontmatter>
---

# Email: <SUBJECT>

## Summary
<ONE sentence that captures who sent it, what they want, and why it matters.>

## Sender Information
- **Name**: <Display Name or "Unknown">
- **Email**: <sender@example.com>
- **Trust Level**: <VIP|KNOWN|UNKNOWN|SPAM>
- **Previous Emails**: <count if determinable from whitelist entry, otherwise "Unknown">

## Content Analysis

**Key Points:**
- <Point 1>
- <Point 2>

**Action Items:**
- [ ] <Action 1>
- [ ] <Action 2>

**Deadlines:**
- <Deadline description>: <date or "None identified">

## Recommended Response
<Suggested action or reply text. State "No response required." if informational only.>

## Next Steps
<What the orchestrator or user should do with this email next.>

---
*Original email body:*

<FULL EMAIL BODY TEXT>
```

## Routing Guidance (for orchestrator)

After writing the output, set the following so the orchestrator knows where to route:

| Priority | status field | orchestrator action |
|----------|-------------|---------------------|
| URGENT   | `triaged`   | Leave in Needs_Action for immediate pick-up |
| HIGH     | `triaged`   | Leave in Needs_Action for next batch |
| NORMAL   | `triaged`   | Move to Inbox for scheduled processing |
| LOW      | `triaged`   | Move to Inbox for batch processing |
| SPAM     | `triaged`   | Move to Archive |

## Special Rules
- NEVER auto-reply to any email. All outbound communication requires HITL approval.
- NEVER delete emails outright; always archive SPAM so the user can review.
- Emails mentioning any financial amount > $500 must be at least HIGH priority.
- Any email with an attachment named `invoice`, `contract`, or `agreement` must be HIGH.
- If whitelist/blacklist files do not exist, treat all senders as UNKNOWN and log a warning.
- If the email body is empty or unreadable, set `priority: NORMAL`, `category: FYI`,
  and note "Email body could not be read — manual review required" in the Summary.
- Do not modify the original email file. Only write to the metadata `.md` file.
