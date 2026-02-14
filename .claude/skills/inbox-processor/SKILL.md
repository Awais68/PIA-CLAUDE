# Inbox Processor Skill

## Description

Processes documents dropped into the Zoya vault. Reads the file, generates a summary, extracts action items, categorizes the document, assigns priority, and writes the results back to the metadata file.

## Trigger

Called by the orchestrator when a metadata file in `/In_Progress/` needs processing.

## Inputs

The orchestrator provides:
- **File to process:** Path to the original document (PDF, DOCX, or Markdown)
- **Metadata file:** Path to the `.md` metadata file to update with results
- **Original filename:** The name the user dropped into Inbox

## Instructions

1. **Read** the document at the provided file path.
   - For `.pdf` files: Read the PDF content. If the PDF is scanned/image-only and returns no text, write `summary: "Scanned PDF — manual review required"` and set `type: other`.
   - For `.docx` files: Read the document text content.
   - For `.md` files: Read the markdown content.

2. **Summarize** the document in 2-3 sentences. Focus on: what is it, who is it from/about, what does it want.

3. **Extract action items** — look for:
   - Explicit tasks or requests ("please send", "action required")
   - Deadlines or due dates
   - Follow-ups needed
   - Payment amounts or invoice numbers
   - Format as markdown checkboxes: `- [ ] action item`

4. **Categorize** as one of: `invoice`, `contract`, `proposal`, `receipt`, `note`, `other`
   - Choose based on content, not just filename
   - Write a one-line explanation of why this category was chosen

5. **Assign priority:**
   - `high` — invoices, contracts, anything with a deadline within 7 days
   - `medium` — proposals, requests
   - `low` — receipts, notes, general documents

6. **Write results** back to the metadata file using this exact format:

```markdown
---
type: <invoice|contract|proposal|receipt|note|other>
original_name: <from existing frontmatter>
queued_name: <from existing frontmatter>
size_bytes: <from existing frontmatter>
content_hash: <from existing frontmatter>
queued_at: <from existing frontmatter>
status: done
retry_count: <from existing frontmatter>
priority: <high|medium|low>
processed_at: <current ISO timestamp>
---

## Summary
<2-3 sentence summary of the document>

## Action Items
- [ ] <extracted action 1>
- [ ] <extracted action 2>

## Category
<one-line explanation of why this categorization was chosen>
```

## Important Rules

- **Preserve** all existing frontmatter fields — only add/update, never remove.
- **Do NOT** move files between folders. The orchestrator handles file movement.
- **Do NOT** modify the original document, only the metadata `.md` file.
- If you cannot read the file (corrupt, empty, password-protected), set `type: other`, `priority: low`, and write `Summary: File could not be read — manual review required.`
