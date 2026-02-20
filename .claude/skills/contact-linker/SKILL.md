# Contact Linker Skill

## Purpose
Links related items across WhatsApp, Gmail, and file channels by building
a contact registry in `AI_Employee_Vault/Contacts/`.

When Zoya processes an email from alice@example.com and later receives a WhatsApp
message from the same person, this skill connects them into a unified contact record.

## When This Skill Is Used
- Automatically called after each item is processed (orchestrator run_cycle)
- Can be run standalone: `uv run python -c "from src.cross_domain_linker import build_contact_graph; build_contact_graph()"`
- Run after importing historical items

## Identity Resolution

| Channel | Identity Key | Extraction Method |
|---------|-------------|------------------|
| Gmail | Email address | Parsed from `sender` frontmatter |
| WhatsApp | Phone number | Normalized E.164 from `sender` |
| File Drop | (not linked) | No reliable identity — skipped |

## Contact Record Format

Contact files are created at:
```
AI_Employee_Vault/Contacts/CONTACT_<key>.md
```

Example key: `alice_at_example_com` (for alice@example.com)

```markdown
---
identity: alice@example.com
display_name: alice@example.com
channels: gmail, whatsapp
created_at: 2026-02-18T12:00:00+00:00
last_seen: 2026-02-19T09:30:00+00:00
interaction_count: 5
---

# Contact: alice@example.com

**Identity:** `alice@example.com`
**Channels:** gmail, whatsapp
**First seen:** 2026-02-18
**Last seen:** 2026-02-19
**Interactions:** 5

## Interactions

- [2026-02-18T12:00] [gmail] invoice: Invoice_Feb.pdf
- [2026-02-19T09:30] [whatsapp] text: wa_message.md
```

## Processing Steps
1. Read frontmatter from the processed item
2. Extract identity from `sender` field based on source channel
3. Look up existing contact record (or create new)
4. Add the new channel to the contact's channel list
5. Append the interaction entry
6. Save the updated contact record

## Special Rules
- File drop items are NOT linked (no reliable identity)
- Phone numbers normalized to digits + leading + only
- Email addresses normalized to lowercase
- Each contact stores last 50 interactions (older ones dropped)
- Contact files are NOT processed by the orchestrator (not in the workflow queue)
- Cross-channel linking is best-effort — no alerts on identity failures
