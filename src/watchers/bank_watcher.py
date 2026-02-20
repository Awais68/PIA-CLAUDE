"""Bank / Finance Statement Watcher — Zoya Gold Tier.

Watches AI_Employee_Vault/Inbox/Bank/ for new CSV or OFX/QFX bank statement
files, parses every transaction, and writes one FILE_*.md directly to Done/
per transaction. Original files are archived to AI_Employee_Vault/Archive/Bank/.

Supported formats (auto-detected):
    CSV — Generic (column-name detection)
    CSV — Revolut   (Type, Started Date, Description, Amount, Currency, …)
    CSV — Starling  (Date, Counter Party, Reference, Type, Amount (GBP), …)
    CSV — HSBC      (Date, Description, Paid out, Paid in, Running Balance)
    OFX / QFX       (standard Open Financial Exchange XML-like format)

Deduplication:
    SHA-256 hash of (date + payee + amount_str + reference) is stored in
    AI_Employee_Vault/Archive/Bank/.seen_hashes to persist across restarts.
    Duplicate transactions are silently skipped.

Entry point:
    uv run zoya-bank

.env variables:
    BANK_POLL_INTERVAL=120   # seconds between folder scans (default 120)
    BANK_DRY_RUN=true        # log transactions without writing files
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from src.audit_logger import audit_log
from src.config import DONE, VAULT_PATH
from src.utils import log_action, setup_logger
from src.watchers.base_watcher import BaseWatcher

import os
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger("bank_watcher")

BANK_INBOX   = VAULT_PATH / "Inbox" / "Bank"
BANK_ARCHIVE = VAULT_PATH / "Archive" / "Bank"
SEEN_HASHES_FILE = BANK_ARCHIVE / ".seen_hashes.json"

BANK_POLL_INTERVAL = int(os.getenv("BANK_POLL_INTERVAL", "120"))
BANK_DRY_RUN = os.getenv("BANK_DRY_RUN", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Transaction dataclass (plain dict for simplicity)
# ---------------------------------------------------------------------------

def _make_txn(
    date: str,
    amount: float,
    payee: str,
    description: str,
    reference: str = "",
    currency: str = "GBP",
    txn_type: str = "",
    balance: float | None = None,
) -> dict:
    return {
        "date": date,
        "amount": round(amount, 2),
        "payee": payee.strip(),
        "description": description.strip(),
        "reference": reference.strip(),
        "currency": currency.upper(),
        "txn_type": txn_type,
        "balance": balance,
    }


def _txn_hash(txn: dict) -> str:
    """SHA-256 of the key transaction fields for deduplication."""
    raw = f"{txn['date']}|{txn['payee']}|{txn['amount']}|{txn['reference']}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Format parsers
# ---------------------------------------------------------------------------

class _FormatError(Exception):
    """Raised when a file cannot be parsed by a given parser."""


def _clean_amount(raw: str) -> float:
    """Parse a currency string like '£1,234.56' or '-34.00' to float."""
    raw = raw.strip().replace(",", "").replace(" ", "")
    raw = re.sub(r"[£€$¥₹]", "", raw)
    try:
        return float(raw)
    except ValueError:
        raise _FormatError(f"Cannot parse amount: {raw!r}")


def _clean_date(raw: str) -> str:
    """Normalise various date formats to YYYY-MM-DD."""
    raw = raw.strip()
    # ISO already
    if re.match(r"\d{4}-\d{2}-\d{2}", raw):
        return raw[:10]
    # DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})", raw)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    # MM/DD/YYYY (US)
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if m:
        mo, d, y = m.groups()
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    # OFX: YYYYMMDD or YYYYMMDDHHMMSS
    m = re.match(r"(\d{4})(\d{2})(\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    raise _FormatError(f"Cannot parse date: {raw!r}")


# ---- Generic CSV --------------------------------------------------------

def _detect_columns(header: list[str]) -> dict[str, int] | None:
    """Map logical field names to column indices via fuzzy matching."""
    h = [c.lower().strip() for c in header]

    def _find(*candidates) -> int | None:
        for c in candidates:
            for i, col in enumerate(h):
                if c in col:
                    return i
        return None

    date_col   = _find("date", "posted", "transaction date", "started date", "completed date")
    amount_col = _find("amount", "paid in", "paid out", "credit", "debit", "value")
    payee_col  = _find("payee", "counter party", "description", "name", "merchant", "narrative")
    desc_col   = _find("memo", "reference", "notes", "details")

    if date_col is None or amount_col is None:
        return None

    return {
        "date":   date_col,
        "amount": amount_col,
        "payee":  payee_col if payee_col is not None else amount_col,
        "desc":   desc_col if desc_col is not None else -1,
    }


def parse_generic_csv(content: str, filename: str = "") -> list[dict]:
    """Parse a generic CSV bank statement."""
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return []

    header = rows[0]
    cols = _detect_columns(header)
    if cols is None:
        raise _FormatError("Cannot identify required columns (date, amount) in CSV")

    transactions = []
    for row in rows[1:]:
        if not row or all(c.strip() == "" for c in row):
            continue
        try:
            date  = _clean_date(row[cols["date"]])
            raw_a = row[cols["amount"]] if cols["amount"] < len(row) else "0"
            # Some banks have separate "paid in" / "paid out" columns
            amount = _clean_amount(raw_a) if raw_a.strip() else 0.0
            payee = row[cols["payee"]] if cols["payee"] < len(row) else ""
            desc  = row[cols["desc"]] if cols["desc"] >= 0 and cols["desc"] < len(row) else ""
            transactions.append(_make_txn(date=date, amount=amount, payee=payee, description=desc))
        except (_FormatError, IndexError):
            continue

    return transactions


# ---- Revolut CSV --------------------------------------------------------
# Columns: Type, Product, Started Date, Completed Date, Description, Amount, Fee, Currency, State, Balance

def parse_revolut_csv(content: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(content))
    transactions = []
    for row in reader:
        try:
            if row.get("State", "").lower() not in ("completed", ""):
                continue
            date   = _clean_date(row.get("Completed Date") or row.get("Started Date", ""))
            amount = _clean_amount(row.get("Amount", "0"))
            payee  = row.get("Description", "").strip()
            curr   = row.get("Currency", "GBP")
            bal_raw = row.get("Balance", "")
            bal    = _clean_amount(bal_raw) if bal_raw.strip() else None
            txn_type = row.get("Type", "")
            transactions.append(_make_txn(
                date=date, amount=amount, payee=payee,
                description=payee, currency=curr,
                txn_type=txn_type, balance=bal,
            ))
        except (_FormatError, KeyError):
            continue
    return transactions


# ---- Starling CSV -------------------------------------------------------
# Columns: Date, Counter Party, Reference, Type, Amount (GBP), Balance (GBP), Spending Category, Notes

def parse_starling_csv(content: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(content))
    transactions = []
    for row in reader:
        try:
            # Starling amounts are already signed (+income / -expense)
            amount_col = next((k for k in row if "amount" in k.lower()), None)
            bal_col    = next((k for k in row if "balance" in k.lower()), None)
            if amount_col is None:
                continue
            date   = _clean_date(row.get("Date", ""))
            amount = _clean_amount(row[amount_col])
            payee  = row.get("Counter Party", "").strip()
            ref    = row.get("Reference", "").strip()
            bal    = _clean_amount(row[bal_col]) if bal_col and row.get(bal_col, "").strip() else None
            txn_type = row.get("Type", "")
            transactions.append(_make_txn(
                date=date, amount=amount, payee=payee,
                description=ref, reference=ref,
                txn_type=txn_type, balance=bal,
            ))
        except (_FormatError, KeyError):
            continue
    return transactions


# ---- HSBC CSV -----------------------------------------------------------
# HSBC exports a weird format: Date,Description (payee),,Paid out,Paid in,Running Balance
# Sometimes has 2-row header or blank leading rows

def parse_hsbc_csv(content: str) -> list[dict]:
    lines = [l for l in content.splitlines() if l.strip()]
    # Find the header line containing "Date"
    header_idx = next(
        (i for i, l in enumerate(lines) if re.search(r"\bDate\b", l, re.IGNORECASE)), None
    )
    if header_idx is None:
        raise _FormatError("No HSBC header row found")

    data = "\n".join(lines[header_idx:])
    reader = csv.reader(io.StringIO(data))
    rows = list(reader)
    header = [c.strip() for c in rows[0]]

    # Find column indices
    def _ci(*names: str) -> int | None:
        for n in names:
            for i, h in enumerate(header):
                if n.lower() in h.lower():
                    return i
        return None

    date_i    = _ci("date")
    payee_i   = _ci("description", "payee", "narrative")
    paid_out_i = _ci("paid out", "debit")
    paid_in_i  = _ci("paid in", "credit")
    bal_i     = _ci("balance", "running balance")

    if date_i is None:
        raise _FormatError("HSBC: cannot find Date column")

    transactions = []
    for row in rows[1:]:
        if not row or all(c.strip() == "" for c in row):
            continue
        try:
            date  = _clean_date(row[date_i])
            payee = row[payee_i].strip() if payee_i is not None and payee_i < len(row) else ""
            out   = _clean_amount(row[paid_out_i]) if paid_out_i is not None and row[paid_out_i].strip() else 0.0
            inc   = _clean_amount(row[paid_in_i])  if paid_in_i  is not None and row[paid_in_i].strip()  else 0.0
            amount = inc - out  # positive = income, negative = expense
            bal   = _clean_amount(row[bal_i]) if bal_i is not None and bal_i < len(row) and row[bal_i].strip() else None
            transactions.append(_make_txn(
                date=date, amount=amount, payee=payee,
                description=payee, balance=bal,
            ))
        except (_FormatError, IndexError):
            continue
    return transactions


# ---- OFX / QFX ----------------------------------------------------------

def parse_ofx(content: str) -> list[dict]:
    """Parse OFX/QFX (Open Financial Exchange) format.

    OFX is a tag-based format similar to XML:
      <STMTTRN>
        <TRNTYPE>DEBIT
        <DTPOSTED>20260115120000
        <TRNAMT>-45.99
        <FITID>20260115-001
        <NAME>Amazon
        <MEMO>Online purchase
      </STMTTRN>
    """
    def _tag(name: str, block: str) -> str:
        m = re.search(rf"<{name}>\s*([^\n<]+)", block, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    # Find all <STMTTRN> ... </STMTTRN> blocks
    blocks = re.findall(r"<STMTTRN>(.*?)</STMTTRN>", content, re.DOTALL | re.IGNORECASE)

    transactions = []
    for block in blocks:
        try:
            dt_raw  = _tag("DTPOSTED", block) or _tag("DTUSER", block)
            amt_raw = _tag("TRNAMT", block)
            name    = _tag("NAME", block)
            memo    = _tag("MEMO", block)
            fitid   = _tag("FITID", block)
            ttype   = _tag("TRNTYPE", block)
            curr    = _tag("CURRENCY", block) or "GBP"

            if not dt_raw or not amt_raw:
                continue

            date   = _clean_date(dt_raw)
            amount = _clean_amount(amt_raw)
            payee  = name or memo or "Unknown"
            transactions.append(_make_txn(
                date=date, amount=amount, payee=payee,
                description=memo, reference=fitid,
                currency=curr, txn_type=ttype,
            ))
        except (_FormatError, Exception):
            continue

    if not blocks:
        raise _FormatError("No <STMTTRN> blocks found — not a valid OFX file")

    return transactions


# ---------------------------------------------------------------------------
# Format detection + dispatch
# ---------------------------------------------------------------------------

def _detect_and_parse(path: Path) -> list[dict]:
    """Auto-detect format and parse all transactions from path."""
    suffix = path.suffix.lower()
    content = path.read_text(encoding="utf-8", errors="replace")

    # OFX / QFX
    if suffix in (".ofx", ".qfx") or "<OFX>" in content or "<STMTTRN>" in content:
        logger.info("Detected OFX format: %s", path.name)
        return parse_ofx(content)

    # CSV format detection
    if suffix == ".csv" or "," in content[:500]:
        first_line = content.splitlines()[0].lower() if content.strip() else ""

        # Revolut: has "Started Date" and "Currency" and "State" headers
        if "started date" in first_line and "state" in first_line:
            logger.info("Detected Revolut CSV: %s", path.name)
            return parse_revolut_csv(content)

        # Starling: has "Counter Party" and "Spending Category"
        if "counter party" in first_line or "spending category" in first_line:
            logger.info("Detected Starling CSV: %s", path.name)
            return parse_starling_csv(content)

        # HSBC: has "Paid out" and "Paid in" in same header, often with Running Balance
        if ("paid out" in first_line or "paid in" in first_line):
            logger.info("Detected HSBC CSV: %s", path.name)
            try:
                return parse_hsbc_csv(content)
            except _FormatError:
                pass  # fall through to generic

        # Generic CSV fallback
        logger.info("Using generic CSV parser: %s", path.name)
        return parse_generic_csv(content, filename=path.name)

    raise _FormatError(f"Unrecognised file format: {path.name} ({suffix})")


# ---------------------------------------------------------------------------
# Transaction file writer
# ---------------------------------------------------------------------------

def _write_transaction_file(txn: dict, source_filename: str) -> Path:
    """Write a single bank transaction to Done/ as a FILE_*.md."""
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S_%f")[:21]  # trim microseconds

    # Safe payee for filename
    safe_payee = re.sub(r"[^\w]", "_", txn["payee"])[:30].strip("_")
    filename = f"FILE_{ts}_bank_{safe_payee}.md"
    dest = DONE / filename

    direction = "income" if txn["amount"] >= 0 else "expense"
    balance_line = f"balance: {txn['balance']}\n" if txn.get("balance") is not None else ""

    content = (
        f"---\n"
        f"type: bank_transaction\n"
        f"source: bank\n"
        f"date: {txn['date']}\n"
        f"amount: {txn['amount']}\n"
        f"currency: {txn['currency']}\n"
        f"direction: {direction}\n"
        f"payee: {txn['payee']}\n"
        f"description: {txn['description']}\n"
        f"reference: {txn['reference']}\n"
        f"txn_type: {txn['txn_type']}\n"
        f"{balance_line}"
        f"source_file: {source_filename}\n"
        f"processed_at: {now.isoformat()}\n"
        f"status: done\n"
        f"priority: {'high' if abs(txn['amount']) > 1000 else 'medium' if abs(txn['amount']) > 100 else 'low'}\n"
        f"---\n\n"
        f"# Bank Transaction: {txn['payee']}\n\n"
        f"| Field | Value |\n"
        f"|-------|-------|\n"
        f"| Date | {txn['date']} |\n"
        f"| Amount | {txn['currency']} {txn['amount']:+.2f} |\n"
        f"| Direction | {direction.upper()} |\n"
        f"| Payee | {txn['payee']} |\n"
        f"| Description | {txn['description'] or '—'} |\n"
        f"| Reference | {txn['reference'] or '—'} |\n"
        f"| Type | {txn['txn_type'] or '—'} |\n"
        + (f"| Balance | {txn['currency']} {txn['balance']:,.2f} |\n" if txn.get("balance") is not None else "")
        + f"\n_Parsed from `{source_filename}` by Zoya Bank Watcher_\n"
    )

    if not BANK_DRY_RUN:
        DONE.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    else:
        logger.info("[DRY RUN] Would write: %s (amount=%+.2f %s %s)",
                    filename, txn["amount"], txn["currency"], txn["payee"])
        # Still return a path for logging
        dest = DONE / filename

    return dest


# ---------------------------------------------------------------------------
# Seen-hash persistence
# ---------------------------------------------------------------------------

def _load_seen_hashes() -> set[str]:
    BANK_ARCHIVE.mkdir(parents=True, exist_ok=True)
    if SEEN_HASHES_FILE.exists():
        try:
            return set(json.loads(SEEN_HASHES_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def _save_seen_hashes(hashes: set[str]) -> None:
    BANK_ARCHIVE.mkdir(parents=True, exist_ok=True)
    SEEN_HASHES_FILE.write_text(
        json.dumps(sorted(hashes), indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Bank Watcher class
# ---------------------------------------------------------------------------

class BankWatcher(BaseWatcher):
    """Watches AI_Employee_Vault/Inbox/Bank/ for bank statement files."""

    name = "bank"

    def __init__(self) -> None:
        super().__init__(poll_interval=BANK_POLL_INTERVAL)
        self._seen_hashes: set[str] = set()

    def setup(self) -> None:
        BANK_INBOX.mkdir(parents=True, exist_ok=True)
        BANK_ARCHIVE.mkdir(parents=True, exist_ok=True)
        DONE.mkdir(parents=True, exist_ok=True)
        self._seen_hashes = _load_seen_hashes()
        self.logger.info(
            "Bank watcher ready — inbox=%s dry_run=%s seen_hashes=%d",
            BANK_INBOX, BANK_DRY_RUN, len(self._seen_hashes),
        )

    def poll(self) -> int:
        """Scan Inbox/Bank/ for new statement files, parse, and write transactions."""
        count = 0
        patterns = ["*.csv", "*.CSV", "*.ofx", "*.OFX", "*.qfx", "*.QFX"]
        files: list[Path] = []
        for pat in patterns:
            files.extend(BANK_INBOX.glob(pat))

        if not files:
            return 0

        self.logger.info("Found %d statement file(s) to process", len(files))
        new_hashes: set[str] = set()

        for stmt_file in sorted(files):
            try:
                transactions = _detect_and_parse(stmt_file)
            except Exception as exc:
                self.logger.error("Failed to parse %s: %s", stmt_file.name, exc)
                audit_log(
                    "bank_parse_error", str(stmt_file),
                    actor="watcher", result="failure", error=str(exc)[:200],
                )
                continue

            self.logger.info("Parsed %d transaction(s) from %s", len(transactions), stmt_file.name)
            file_new = 0
            file_dup = 0

            for txn in transactions:
                h = _txn_hash(txn)
                if h in self._seen_hashes:
                    file_dup += 1
                    continue

                try:
                    dest = _write_transaction_file(txn, stmt_file.name)
                    new_hashes.add(h)
                    count += 1
                    file_new += 1

                    audit_log(
                        "bank_transaction_processed",
                        dest.name,
                        actor="watcher",
                        parameters={
                            "date": txn["date"],
                            "amount": txn["amount"],
                            "currency": txn["currency"],
                            "payee": txn["payee"][:50],
                            "source_file": stmt_file.name,
                            "dry_run": BANK_DRY_RUN,
                        },
                    )
                except Exception as exc:
                    self.logger.error("Failed to write transaction: %s — %s", txn, exc)

            self.logger.info(
                "%s: %d new, %d duplicates skipped",
                stmt_file.name, file_new, file_dup,
            )

            # Archive the statement file
            _archive_statement(stmt_file)

        # Persist new hashes
        if new_hashes:
            self._seen_hashes |= new_hashes
            _save_seen_hashes(self._seen_hashes)

        return count

    def teardown(self) -> None:
        _save_seen_hashes(self._seen_hashes)


def _archive_statement(path: Path) -> None:
    """Move a processed statement to Archive/Bank/."""
    BANK_ARCHIVE.mkdir(parents=True, exist_ok=True)
    dest = BANK_ARCHIVE / path.name
    # Add timestamp prefix if collision
    if dest.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_")
        dest = BANK_ARCHIVE / (ts + path.name)
    if not BANK_DRY_RUN:
        shutil.move(str(path), dest)
        logger.info("Archived statement: %s → %s", path.name, dest.name)
    else:
        logger.info("[DRY RUN] Would archive: %s", path.name)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the Bank Statement Watcher."""
    watcher = BankWatcher()
    watcher.start()


if __name__ == "__main__":
    main()
