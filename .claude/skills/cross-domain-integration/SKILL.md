# Cross-Domain Integration Skill

## Purpose
Bridges Zoya's personal and business domains. Detects when personal-channel
items (WhatsApp, bank transactions) contain business-relevant content and
automatically creates or updates business-domain records.

## Domains

| Domain | Channels | Storage |
|--------|----------|---------|
| Personal | Gmail, WhatsApp, bank | Done/ (processed items) |
| Business | Social media, invoices, project tasks | Business/Tasks/, Clients/ |

## When This Skill Is Used
- Integrated into orchestrator's `run_cycle()` after items are moved to Done/
- Can be run standalone: `uv run python -m src.cross_domain_orchestrator`
- Run by cron for periodic cross-domain sync

## Bridge Rules

### Rule 1: WhatsApp → Business Task
**Trigger:** A WhatsApp message in Done/ contains one or more business keywords.

**Business keywords:**
`invoice`, `payment`, `project`, `client`, `contract`, `deadline`,
`proposal`, `budget`, `quote`, `deliverable`, `milestone`, `retainer`,
`fee`, `billing`

**Action:** Creates `TASK_<timestamp>_<name>.md` in `AI_Employee_Vault/Business/Tasks/`

**Task file contains:**
- Sender, timestamp, matched keywords
- Summary extracted from the processed WhatsApp message
- Action items pre-populated
- Original message excerpt (first 800 chars)

**Deduplication:** Each source item is only processed once. State tracked in
`AI_Employee_Vault/Logs/.cross_domain_processed.json`.

### Rule 2: Bank Transaction → Client Ledger
**Trigger:** A bank transaction item in Done/ has a payee matching a known client.

**Match logic:**
1. Exact match: payee name == client name (case-insensitive)
2. Substring match: client name contained in payee, or vice versa

**Client records:** `AI_Employee_Vault/Clients/CLIENT_<name>.md`

**Action:** Appends a ledger row to the matching client's `## Ledger` section:
```
| Date | Transaction | Amount | Description |
```

**Bank transaction detection:** Items with frontmatter `type: bank_transaction`
or `source: bank`, or `type: receipt` / `type: invoice`.

## File Locations

```
AI_Employee_Vault/
├── Business/
│   └── Tasks/
│       └── TASK_<timestamp>_<source_name>.md   # Auto-created tasks
├── Clients/
│   └── CLIENT_<name>.md                        # Client records with ledger
└── Logs/
    └── .cross_domain_processed.json            # Dedup state (hidden file)
```

## Client Record Format
```markdown
---
client_name: Acme Corp
email: billing@acme.com
phone: +1234567890
created_at: 2026-02-20T10:00:00+00:00
last_transaction: 2026-02-20
---

# Client: Acme Corp

**Email:** billing@acme.com
**Phone:** +1234567890
**Since:** 2026-02-20

## Notes
Freelance client, net-30 payment terms.

## Ledger

| Date | Transaction | Amount | Description |
|------|-------------|--------|-------------|
| 2026-02-20 | Invoice_Feb.pdf | 1500 | Monthly retainer |
```

## Business Task Format
```markdown
---
type: business_task
source: whatsapp
sender: +441234567890
created_at: 2026-02-20T10:00:00+00:00
status: pending
triggered_by: wa_message.md
keywords_matched: invoice, payment
---

# Business Task (auto-created from WhatsApp)

**From:** +441234567890
**Keywords matched:** invoice, payment

## Summary
Client asking about outstanding invoice for February.

## Original Message Excerpt
...
```

## Creating Clients Manually
```python
from src.cross_domain_orchestrator import create_client
create_client("Acme Corp", email="billing@acme.com", phone="+1234567890")
```

## Special Rules
- WhatsApp items are scanned ONCE after landing in Done/
- Bank transactions need `type: bank_transaction` in frontmatter (set by inbox-processor)
- Client matching is best-effort; no alerts on failed matches
- Tasks are created in Business/Tasks/ — NOT in the main queue (not processed by orchestrator)
- Client ledger entries append-only; never modified or deleted
