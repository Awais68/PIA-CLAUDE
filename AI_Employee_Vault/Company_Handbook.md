---
last_updated: 2026-02-14
review_frequency: monthly
---

# Company Handbook - Zoya Rules of Engagement

## Document Processing Rules

| Rule | Setting |
|------|---------|
| Auto-categorize all dropped documents | Yes |
| Always extract deadlines and tasks | Yes |
| Flag invoices and contracts as high priority | Yes |
| Summary length | 2-3 sentences |
| Update dashboard after every processed item | Yes |
| Keep all processed files in /Done/ | Yes |
| Log every action to /Logs/ | Yes |

## Document Categories

| Category | Description | Priority |
|----------|-------------|----------|
| invoice | Bills, payment requests | high |
| contract | Legal agreements, SOWs | high |
| proposal | Business proposals, quotes | medium |
| receipt | Payment confirmations, receipts | low |
| note | Meeting notes, memos, general notes | low |
| other | Anything that doesn't fit above | low |

## Supported File Types

| Extension | Handling |
|-----------|---------|
| .pdf | Read and summarize. Flag scanned/image-only PDFs for manual review. |
| .docx | Read and summarize. |
| .md | Read and summarize. |
| Other | Move to /Quarantine/ with note: "Unsupported file type" |

## Processing Limits

| Limit | Value |
|-------|-------|
| Max file size for processing | 10 MB |
| Max retries before quarantine | 3 |
| File stability wait time | 2 seconds |
| Max files per processing batch | 10 |

## Priority Rules

- Invoices with amounts > $500: **high**
- Contracts with deadlines within 7 days: **high**
- All other invoices and contracts: **high**
- Proposals: **medium**
- Everything else: **low**
