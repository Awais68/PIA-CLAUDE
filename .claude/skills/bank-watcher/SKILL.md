---
skill_name: BankWatcher
version: 1.0
trigger: "Automatic — polls AI_Employee_Vault/Inbox/Bank/ every 120s (BANK_POLL_INTERVAL)"
inputs: CSV or OFX/QFX bank statement files dropped in /Vault/Inbox/Bank/
outputs: One FILE_*.md per transaction written directly to /Vault/Done/; originals archived to /Vault/Archive/Bank/
approval_required: "no — read-only parsing; no external actions taken"
max_runtime: 5
---

## Objective

Parse bank statement files (CSV, OFX, QFX) into individual structured transaction
records in `/Vault/Done/`, enabling the CEO Briefing and audit systems to see
real financial data without any manual data entry.

## Supported Formats (Auto-detected)

| Format | Detection | Parser |
|--------|-----------|--------|
| Generic CSV | Column name fuzzy-match | `parse_generic_csv` |
| Revolut CSV | "Started Date" + "State" columns | `parse_revolut_csv` |
| Starling CSV | "Counter Party" + "Spending Category" | `parse_starling_csv` |
| HSBC CSV | "Paid out" + "Paid in" columns | `parse_hsbc_csv` |
| OFX / QFX | `<STMTTRN>` tags or `.ofx`/`.qfx` suffix | `parse_ofx` |

## Step-by-Step Process

1. **Watch** `AI_Employee_Vault/Inbox/Bank/` for `*.csv`, `*.ofx`, `*.qfx` files

2. **Detect format** — check filename suffix and first-line headers

3. **Parse** all transactions from the file

4. **Deduplicate** using SHA-256 of `date + payee + amount + reference`
   - Seen hashes persisted to `Archive/Bank/.seen_hashes.json` across restarts
   - Duplicate transactions silently skipped

5. **Write transaction file** to `/Done/` for each new transaction:
   ```
   FILE_YYYYMMDD_HHMMSS_bank_<payee>.md
   ```
   With frontmatter:
   ```yaml
   type: bank_transaction
   date: YYYY-MM-DD
   amount: float (positive=income, negative=expense)
   currency: GBP
   direction: income|expense
   payee: string
   description: string
   reference: string
   txn_type: DEBIT|CREDIT|...
   balance: float (if available)
   source_file: original_filename.csv
   processed_at: ISO timestamp
   status: done
   priority: high|medium|low  (based on abs(amount))
   ```

6. **Archive** the original statement file to `Archive/Bank/`

7. **Log** every transaction to audit_logger (`bank_transaction_processed`)

## Priority Assignment

| Amount | Priority |
|--------|----------|
| > £1,000 (abs) | high |
| £100–£1,000 (abs) | medium |
| < £100 (abs) | low |

## .env Variables

```
BANK_POLL_INTERVAL=120   # seconds between folder scans
BANK_DRY_RUN=true        # log transactions without writing files
```

## How to Start

```bash
# Start the bank watcher
uv run zoya-bank

# Or via entry point
uv run python -m src.watchers.bank_watcher
```

## How to Test

1. Drop a test CSV in `AI_Employee_Vault/Inbox/Bank/test.csv`:
   ```csv
   Date,Description,Amount
   2026-02-20,Amazon UK,-45.99
   2026-02-20,Salary payment,3500.00
   ```
2. Watch logs: `tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).log`
3. Check `AI_Employee_Vault/Done/` for `FILE_*_bank_*.md` files

## Success Criteria

- All non-duplicate transactions appear as `FILE_*.md` in Done/
- `type: bank_transaction` in frontmatter
- Original statement moved to `Archive/Bank/`
- `.seen_hashes.json` updated with new hashes
- Audit log entry `bank_transaction_processed` per transaction

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| Unrecognised format | Skip file, log error, leave in Inbox/Bank/ |
| Malformed row | Skip row, continue with remaining rows |
| Duplicate transaction | Skip silently (dedup by hash) |
| Disk full | Raise immediately, leave original untouched |
| Date parse failure | Skip row, log warning |

## Sample Transaction File Output

```markdown
---
type: bank_transaction
source: bank
date: 2026-02-20
amount: -45.99
currency: GBP
direction: expense
payee: Amazon UK
description: Amazon UK
reference: REF123456
processed_at: 2026-02-20T14:30:00Z
status: done
priority: low
---

# Bank Transaction: Amazon UK

| Field | Value |
|-------|-------|
| Date | 2026-02-20 |
| Amount | GBP -45.99 |
| Direction | EXPENSE |
| Payee | Amazon UK |
```
