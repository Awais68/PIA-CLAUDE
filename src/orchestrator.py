"""
Orchestrator for Zoya.

Polls Needs_Action/ for pending metadata files and invokes Claude Code
to process them ONE AT A TIME (claim-by-move pattern).

Flow:
  1. Acquire process lock (only one orchestrator at a time).
  2. Poll Needs_Action/ for .md files with status: pending.
  3. Claim a file by moving it + its companion to In_Progress/.
  4. Invoke Claude Code with the inbox-processor skill prompt.
  5. On success: move to Done/.  On failure: increment retry_count
     or quarantine after MAX_RETRIES.
  6. Trigger dashboard-updater skill.
  7. Loop.
"""

import argparse
import atexit
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.config import (
    AI_PROVIDER,
    APPROVED,
    DASHBOARD,
    DASHSCOPE_API_KEY,
    DONE,
    IN_PROGRESS,
    MAX_BATCH_SIZE,
    MAX_RETRIES,
    NEEDS_ACTION,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    ORCHESTRATOR_LOCK,
    ORCHESTRATOR_POLL_INTERVAL,
    PENDING_APPROVAL,
    PLANS,
    PROJECT_ROOT,
    QUARANTINE,
    QWEN_BASE_URL,
    QWEN_MODEL,
    REJECTED,
    VAULT_PATH,
)
from src.utils import acquire_lock, log_action, release_lock, setup_logger

logger = setup_logger("orchestrator")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_frontmatter(path: Path) -> dict[str, str]:
    """Parse YAML-ish frontmatter from a metadata .md file."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip()
    return fm


def _update_frontmatter(path: Path, updates: dict[str, str]) -> None:
    """Update specific keys in the frontmatter of a metadata file."""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return

    fm_lines = match.group(1).splitlines()
    new_lines: list[str] = []
    updated_keys: set[str] = set()
    for line in fm_lines:
        if ":" in line:
            key = line.partition(":")[0].strip()
            if key in updates:
                new_lines.append(f"{key}: {updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Add any keys that weren't already present
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}: {val}")

    new_fm = "---\n" + "\n".join(new_lines) + "\n---"
    rest = text[match.end():]
    path.write_text(new_fm + rest, encoding="utf-8")


def _find_companion(meta_path: Path, source_dir: Path) -> Path | None:
    """Find the original file that accompanies a metadata .md file.

    Metadata file: FILE_20260214_120000_report.md
    Companion:     FILE_20260214_120000_report.pdf (or .docx, etc.)
    """
    stem = meta_path.stem  # e.g. FILE_20260214_120000_report
    for f in source_dir.iterdir():
        if f.stem == stem and f.suffix != ".md":
            return f
    return None


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def claim_file(meta_path: Path) -> tuple[Path, Path | None]:
    """Move metadata + companion from Needs_Action to In_Progress (claim)."""
    new_meta = IN_PROGRESS / meta_path.name
    shutil.move(str(meta_path), new_meta)

    companion = _find_companion(meta_path, NEEDS_ACTION)
    new_companion = None
    if companion and companion.exists():
        new_companion = IN_PROGRESS / companion.name
        shutil.move(str(companion), new_companion)

    _update_frontmatter(new_meta, {"status": "in_progress"})
    log_action("file_claimed", str(new_meta))
    return new_meta, new_companion


def _build_prompt(meta_path: Path, companion: Path | None) -> str:
    """Build the processing prompt for any AI provider."""
    fm = _read_frontmatter(meta_path)
    original_name = fm.get("original_name", meta_path.name)
    source = fm.get("source", "file_drop")
    file_to_read = str(companion) if companion else str(meta_path)

    # Use gmail-processor skill for email-sourced files
    if source == "gmail":
        skill = "gmail-processor"
        categories = "client_email, invoice, newsletter, notification, personal, spam"
    else:
        skill = "inbox-processor"
        categories = "invoice, contract, proposal, receipt, note, other"

    return (
        f"You are Zoya, a Personal AI Employee. "
        f"Process this document using the {skill} skill.\n\n"
        f"**File to process:** `{file_to_read}`\n"
        f"**Metadata file:** `{meta_path}`\n"
        f"**Original filename:** {original_name}\n"
        f"**Source:** {source}\n\n"
        f"Instructions:\n"
        f"1. Read the file at the path above.\n"
        f"2. Generate a 2-3 sentence summary.\n"
        f"3. Extract all action items (deadlines, tasks, follow-ups).\n"
        f"4. Categorize: {categories}.\n"
        f"5. Assign priority: high (invoices, contracts), medium (proposals), low (other).\n"
        f"6. Write the processed results back to the metadata file at `{meta_path}` "
        f"using the format defined in the {skill} skill.\n"
        f"7. Update the frontmatter status to 'done'.\n"
        f"8. Do NOT move files — the orchestrator handles that.\n"
    )


def _read_file_content(companion: Path | None, meta_path: Path) -> str:
    """Read the actual document content for Qwen (which can't read files itself)."""
    target = companion if companion else meta_path
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"[Binary file: {target.name} — {target.stat().st_size} bytes]"
    except OSError as e:
        return f"[Error reading file: {e}]"


def _process_with_qwen(meta_path: Path, companion: Path | None) -> bool:
    """Process a file using Qwen via DashScope API."""
    from openai import OpenAI

    fm = _read_frontmatter(meta_path)
    original_name = fm.get("original_name", meta_path.name)

    logger.info("Invoking Qwen (%s) for: %s", QWEN_MODEL, original_name)

    # Read file content since Qwen can't access local files
    file_content = _read_file_content(companion, meta_path)

    system_prompt = (
        "You are Zoya, a Personal AI Employee. You process documents by "
        "summarizing them, extracting action items, categorizing them, and "
        "assigning priorities. Respond ONLY with the processed metadata in "
        "the exact format shown below — no extra text.\n\n"
        "Output format:\n"
        "---\n"
        "type: <invoice|contract|proposal|receipt|note|other>\n"
        "priority: <high|medium|low>\n"
        "---\n\n"
        "## Summary\n<2-3 sentence summary>\n\n"
        "## Action Items\n- [ ] <action 1>\n- [ ] <action 2>\n...\n\n"
        "## Category\n<brief explanation of category choice>\n"
    )

    user_prompt = (
        f"Process this document:\n\n"
        f"**Original filename:** {original_name}\n\n"
        f"**Document content:**\n```\n{file_content}\n```"
    )

    try:
        client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=QWEN_BASE_URL)
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )
        ai_output = response.choices[0].message.content

        # Parse the AI output and write to metadata file
        _write_qwen_result(meta_path, fm, ai_output)

        logger.info("Qwen processed successfully: %s", original_name)
        return True

    except Exception:
        logger.exception("Qwen failed for %s", original_name)
        return False


def _write_qwen_result(meta_path: Path, fm: dict[str, str], ai_output: str) -> None:
    """Write Qwen's response back to the metadata file."""
    import re as _re

    # Try to extract type and priority from AI output frontmatter
    doc_type = "other"
    priority = "low"
    type_match = _re.search(r"type:\s*(\w+)", ai_output)
    prio_match = _re.search(r"priority:\s*(\w+)", ai_output)
    if type_match:
        doc_type = type_match.group(1)
    if prio_match:
        priority = prio_match.group(1)

    # Remove the AI's frontmatter block from output (keep the rest)
    body = _re.sub(r"^---.*?---\s*", "", ai_output, flags=_re.DOTALL).strip()

    # Build the final metadata file
    now = datetime.now(timezone.utc).isoformat()
    content = (
        f"---\n"
        f"type: {doc_type}\n"
        f"original_name: {fm.get('original_name', meta_path.name)}\n"
        f"queued_name: {fm.get('queued_name', meta_path.name)}\n"
        f"size_bytes: {fm.get('size_bytes', '0')}\n"
        f"content_hash: {fm.get('content_hash', '')}\n"
        f"queued_at: {fm.get('queued_at', now)}\n"
        f"status: done\n"
        f"retry_count: {fm.get('retry_count', '0')}\n"
        f"priority: {priority}\n"
        f"processed_at: {now}\n"
        f"ai_provider: qwen/{QWEN_MODEL}\n"
        f"---\n\n"
        f"{body}\n"
    )
    meta_path.write_text(content, encoding="utf-8")


def _process_with_ollama(meta_path: Path, companion: Path | None) -> bool:
    """Process a file using Qwen via local Ollama."""
    from openai import OpenAI

    fm = _read_frontmatter(meta_path)
    original_name = fm.get("original_name", meta_path.name)

    logger.info("Invoking Ollama (%s) for: %s", OLLAMA_MODEL, original_name)

    file_content = _read_file_content(companion, meta_path)

    system_prompt = (
        "You are Zoya, a Personal AI Employee. You process documents by "
        "summarizing them, extracting action items, categorizing them, and "
        "assigning priorities. Respond ONLY with the processed metadata in "
        "the exact format shown below — no extra text, no thinking tags.\n\n"
        "Output format:\n"
        "---\n"
        "type: <invoice|contract|proposal|receipt|note|other>\n"
        "priority: <high|medium|low>\n"
        "---\n\n"
        "## Summary\n<2-3 sentence summary>\n\n"
        "## Action Items\n- [ ] <action 1>\n- [ ] <action 2>\n...\n\n"
        "## Category\n<brief explanation of category choice>\n"
    )

    user_prompt = (
        f"Process this document:\n\n"
        f"**Original filename:** {original_name}\n\n"
        f"**Document content:**\n```\n{file_content}\n```"
    )

    try:
        client = OpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL)
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        ai_output = response.choices[0].message.content

        # Strip <think>...</think> blocks that some models produce
        ai_output = re.sub(r"<think>.*?</think>", "", ai_output, flags=re.DOTALL).strip()

        _write_ollama_result(meta_path, fm, ai_output)

        logger.info("Ollama processed successfully: %s", original_name)
        return True

    except Exception:
        logger.exception("Ollama failed for %s", original_name)
        return False


def _write_ollama_result(meta_path: Path, fm: dict[str, str], ai_output: str) -> None:
    """Write Ollama's response back to the metadata file."""
    doc_type = "other"
    priority = "low"
    type_match = re.search(r"type:\s*(\w+)", ai_output)
    prio_match = re.search(r"priority:\s*(\w+)", ai_output)
    if type_match:
        doc_type = type_match.group(1)
    if prio_match:
        priority = prio_match.group(1)

    body = re.sub(r"^---.*?---\s*", "", ai_output, flags=re.DOTALL).strip()

    now = datetime.now(timezone.utc).isoformat()
    content = (
        f"---\n"
        f"type: {doc_type}\n"
        f"original_name: {fm.get('original_name', meta_path.name)}\n"
        f"queued_name: {fm.get('queued_name', meta_path.name)}\n"
        f"size_bytes: {fm.get('size_bytes', '0')}\n"
        f"content_hash: {fm.get('content_hash', '')}\n"
        f"queued_at: {fm.get('queued_at', now)}\n"
        f"status: done\n"
        f"retry_count: {fm.get('retry_count', '0')}\n"
        f"priority: {priority}\n"
        f"processed_at: {now}\n"
        f"ai_provider: ollama/{OLLAMA_MODEL}\n"
        f"---\n\n"
        f"{body}\n"
    )
    meta_path.write_text(content, encoding="utf-8")


def _process_with_claude(meta_path: Path, companion: Path | None) -> bool:
    """Process a file using Claude Code CLI."""
    fm = _read_frontmatter(meta_path)
    original_name = fm.get("original_name", meta_path.name)
    prompt = _build_prompt(meta_path, companion)

    logger.info("Invoking Claude Code for: %s", original_name)

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(PROJECT_ROOT),
            env=env,
        )
        if result.returncode == 0:
            logger.info("Claude processed successfully: %s", original_name)
            return True
        else:
            logger.error(
                "Claude failed (exit %d) for %s: %s",
                result.returncode,
                original_name,
                result.stderr[:500],
            )
            return False
    except subprocess.TimeoutExpired:
        logger.error("Claude timed out processing: %s", original_name)
        return False
    except FileNotFoundError:
        logger.error(
            "Claude Code CLI not found. Install with: npm install -g @anthropic/claude-code"
        )
        return False


def process_file(meta_path: Path, companion: Path | None) -> bool:
    """Process a file using the configured AI provider.

    Returns True on success, False on failure.
    """
    if AI_PROVIDER == "ollama":
        return _process_with_ollama(meta_path, companion)
    if AI_PROVIDER == "qwen":
        return _process_with_qwen(meta_path, companion)
    return _process_with_claude(meta_path, companion)


def move_to_done(meta_path: Path, companion: Path | None) -> None:
    """Move processed files from In_Progress to Done."""
    dest_meta = DONE / meta_path.name
    shutil.move(str(meta_path), dest_meta)
    if companion and companion.exists():
        shutil.move(str(companion), DONE / companion.name)
    _update_frontmatter(dest_meta, {
        "status": "done",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    })
    log_action("file_done", str(dest_meta))
    logger.info("Moved to Done: %s", dest_meta.name)


def handle_failure(meta_path: Path, companion: Path | None) -> None:
    """Increment retry count or quarantine after max retries."""
    fm = _read_frontmatter(meta_path)
    retry_count = int(fm.get("retry_count", "0")) + 1

    if retry_count >= MAX_RETRIES:
        logger.warning(
            "Max retries (%d) reached for %s — quarantining",
            MAX_RETRIES,
            meta_path.name,
        )
        shutil.move(str(meta_path), QUARANTINE / meta_path.name)
        if companion and companion.exists():
            shutil.move(str(companion), QUARANTINE / companion.name)
        _update_frontmatter(
            QUARANTINE / meta_path.name,
            {"status": "quarantined", "reason": f"Failed after {MAX_RETRIES} attempts"},
        )
        log_action("file_quarantined", str(meta_path), {"retries": retry_count})
    else:
        # Move back to Needs_Action for retry
        dest = NEEDS_ACTION / meta_path.name
        shutil.move(str(meta_path), dest)
        if companion and companion.exists():
            shutil.move(str(companion), NEEDS_ACTION / companion.name)
        _update_frontmatter(dest, {
            "status": "pending",
            "retry_count": str(retry_count),
        })
        log_action("file_retry", str(dest), {"retry_count": retry_count})
        logger.info("Retry %d/%d for %s", retry_count, MAX_RETRIES, meta_path.name)


def update_dashboard() -> None:
    """Refresh Dashboard.md using the configured AI provider."""
    if AI_PROVIDER in ("qwen", "ollama"):
        _update_dashboard_local()
    else:
        _update_dashboard_claude()


def _update_dashboard_claude() -> None:
    """Update dashboard via Claude Code CLI."""
    prompt = (
        f"You are Zoya. Update the dashboard at `{DASHBOARD}`.\n\n"
        f"1. Count files in each vault folder:\n"
        f"   - Inbox: `{VAULT_PATH / 'Inbox'}`\n"
        f"   - Needs_Action: `{VAULT_PATH / 'Needs_Action'}`\n"
        f"   - In_Progress: `{VAULT_PATH / 'In_Progress'}`\n"
        f"   - Done: `{VAULT_PATH / 'Done'}`\n"
        f"   - Quarantine: `{VAULT_PATH / 'Quarantine'}`\n"
        f"2. List the 10 most recent items in Done/ (read their summaries).\n"
        f"3. Note any items in Quarantine as alerts.\n"
        f"4. Write the updated dashboard to `{DASHBOARD}` using the "
        f"dashboard-updater skill format.\n"
        f"5. Set last_updated in the frontmatter to now.\n"
    )
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(PROJECT_ROOT),
            env=env,
        )
        logger.info("Dashboard updated.")
    except Exception:
        logger.exception("Dashboard update failed (non-critical)")


def _update_dashboard_local() -> None:
    """Update dashboard locally (for Qwen/Ollama) — counts files directly in Python."""
    now = datetime.now(timezone.utc)
    provider_label = f"Ollama ({OLLAMA_MODEL})" if AI_PROVIDER == "ollama" else f"Qwen ({QWEN_MODEL})"
    provider_tag = f"ollama/{OLLAMA_MODEL}" if AI_PROVIDER == "ollama" else f"qwen/{QWEN_MODEL}"

    def _count(folder: Path) -> int:
        return len([f for f in folder.iterdir() if f.is_file() and f.name != ".gitkeep"]) if folder.exists() else 0

    # Count files in each folder
    counts = {
        "Inbox": _count(VAULT_PATH / "Inbox"),
        "Needs_Action": _count(NEEDS_ACTION),
        "In_Progress": _count(IN_PROGRESS),
        "Done": _count(DONE),
        "Quarantine": _count(QUARANTINE),
    }

    # Get recent Done items
    done_files = sorted(DONE.glob("FILE_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
    recent_items = []
    for f in done_files:
        fm = _read_frontmatter(f)
        recent_items.append(
            f"| {fm.get('original_name', f.name)} | {fm.get('type', '?')} | "
            f"{fm.get('priority', '?')} | {fm.get('processed_at', '?')[:19]} |"
        )

    recent_table = "\n".join(recent_items) if recent_items else "| No items yet | | | |"

    # Get quarantine alerts
    q_files = list(QUARANTINE.glob("*.md"))
    alerts = ""
    if q_files:
        alerts = f"\n> **Alerts:** {len(q_files)} item(s) in Quarantine need review.\n"

    dashboard = (
        f"---\nlast_updated: {now.isoformat()}\nai_provider: {provider_tag}\n---\n\n"
        f"# Zoya Dashboard\n\n"
        f"**Last updated:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        f"**AI Provider:** {provider_label}\n\n"
        f"## Queue Status\n\n"
        f"| Folder | Count |\n|--------|-------|\n"
        f"| Inbox | {counts['Inbox']} |\n"
        f"| Needs Action | {counts['Needs_Action']} |\n"
        f"| In Progress | {counts['In_Progress']} |\n"
        f"| Done | {counts['Done']} |\n"
        f"| Quarantine | {counts['Quarantine']} |\n"
        f"{alerts}\n"
        f"## Recent Activity\n\n"
        f"| File | Type | Priority | Processed |\n"
        f"|------|------|----------|-----------|\n"
        f"{recent_table}\n"
    )
    DASHBOARD.write_text(dashboard, encoding="utf-8")
    logger.info("Dashboard updated (%s mode).", AI_PROVIDER)


# ---------------------------------------------------------------------------
# Plan.md reasoning (S4)
# ---------------------------------------------------------------------------

# Document types that warrant a Plan.md before processing
PLAN_TYPES = {"invoice", "contract", "proposal"}

# HITL thresholds
HITL_AMOUNT_THRESHOLD = 500  # dollars
HITL_DEADLINE_DAYS = 7


def should_create_plan(fm: dict[str, str]) -> bool:
    """Determine if a document requires a Plan.md before processing."""
    doc_type = fm.get("type", "").lower()
    if doc_type in PLAN_TYPES:
        return True
    # Gmail emails with approval_required flag
    if fm.get("approval_required") == "true":
        return True
    return False


def create_plan(meta_path: Path, fm: dict[str, str]) -> Path:
    """Generate a Plan.md file in the Plans/ folder for this document.

    Returns the path to the created plan file.
    """
    PLANS.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    original_name = fm.get("original_name", meta_path.name)
    doc_type = fm.get("type", "other")
    priority = fm.get("priority", "low")
    source = fm.get("source", "file_drop")

    # Determine complexity and steps based on doc type
    if doc_type == "invoice":
        complexity = "moderate"
        steps = (
            "1. [ ] Verify invoice sender and amount — owner: ai\n"
            "2. [ ] Cross-reference with Company_Handbook.md — owner: ai\n"
            "3. [ ] Flag for HITL approval if amount > $500 — owner: ai\n"
            "4. [ ] Await human approval — owner: human\n"
            "5. [ ] Process payment or archive — owner: human"
        )
        requires_approval = "true"
    elif doc_type == "contract":
        complexity = "complex"
        steps = (
            "1. [ ] Extract key terms and deadlines — owner: ai\n"
            "2. [ ] Identify obligations and risks — owner: ai\n"
            "3. [ ] Summarize for human review — owner: ai\n"
            "4. [ ] Route to HITL for approval — owner: ai\n"
            "5. [ ] Await human decision — owner: human"
        )
        requires_approval = "true"
    elif doc_type == "proposal":
        complexity = "moderate"
        steps = (
            "1. [ ] Summarize proposal content — owner: ai\n"
            "2. [ ] Extract budget and timeline — owner: ai\n"
            "3. [ ] Assess alignment with business goals — owner: ai\n"
            "4. [ ] Generate response recommendation — owner: ai\n"
            "5. [ ] Route to HITL if response needed — owner: ai"
        )
        requires_approval = priority == "high"
        requires_approval = "true" if requires_approval else "false"
    else:
        complexity = "simple"
        steps = (
            "1. [ ] Analyze document content — owner: ai\n"
            "2. [ ] Categorize and assign priority — owner: ai\n"
            "3. [ ] Extract action items — owner: ai"
        )
        requires_approval = "false"

    plan_name = f"PLAN_{now.strftime('%Y%m%d_%H%M%S')}_{meta_path.stem}.md"
    plan_path = PLANS / plan_name

    content = (
        f"---\n"
        f"task_ref: {fm.get('queued_name', meta_path.name)}\n"
        f"created_at: {now.isoformat()}\n"
        f"complexity: {complexity}\n"
        f"requires_approval: {requires_approval}\n"
        f"source: {source}\n"
        f"status: draft\n"
        f"---\n\n"
        f"## Objective\n"
        f"Process {doc_type} document: {original_name}\n\n"
        f"## Steps\n{steps}\n\n"
        f"## Dependencies\n"
        f"- Steps requiring human approval depend on AI analysis completing first\n\n"
        f"## Risks / Notes\n"
        f"- Priority: {priority}\n"
        f"- Source: {source}\n"
    )
    plan_path.write_text(content, encoding="utf-8")
    log_action("plan_created", str(plan_path), {"task_ref": meta_path.name})
    logger.info("Plan.md created: %s", plan_name)
    return plan_path


# ---------------------------------------------------------------------------
# HITL approval workflow (S6)
# ---------------------------------------------------------------------------

def evaluate_hitl(meta_path: Path) -> bool:
    """Check if a processed file needs HITL approval before completion.

    Returns True if approval is required.
    """
    fm = _read_frontmatter(meta_path)
    doc_type = fm.get("type", "").lower()
    priority = fm.get("priority", "low")
    source = fm.get("source", "file_drop")

    # Explicit flag from processor
    if fm.get("approval_required") == "true":
        return True

    # High-priority invoices and contracts always need approval
    if doc_type in ("invoice", "contract") and priority == "high":
        return True

    # Gmail emails with high priority
    if source == "gmail" and priority == "high":
        return True

    # LinkedIn posts always need approval
    if doc_type == "linkedin_post":
        return True

    return False


def route_to_approval(meta_path: Path, companion: Path | None) -> tuple[Path, Path | None]:
    """Move files from In_Progress to Pending_Approval for human review."""
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)

    dest_meta = PENDING_APPROVAL / meta_path.name
    shutil.move(str(meta_path), dest_meta)

    dest_companion = None
    if companion and companion.exists():
        dest_companion = PENDING_APPROVAL / companion.name
        shutil.move(str(companion), dest_companion)

    _update_frontmatter(dest_meta, {
        "status": "pending_approval",
        "approval_requested_at": datetime.now(timezone.utc).isoformat(),
    })
    log_action("file_routed_to_approval", str(dest_meta))
    logger.info("Routed to approval: %s", dest_meta.name)
    return dest_meta, dest_companion


def process_approved_files() -> int:
    """Check Approved/ for files that have been approved by a human.

    Moves approved files to Done/.
    Returns count of files processed.
    """
    APPROVED.mkdir(parents=True, exist_ok=True)
    count = 0

    for md_file in sorted(APPROVED.glob("FILE_*.md")):
        fm = _read_frontmatter(md_file)
        companion = _find_companion(md_file, APPROVED)

        dest_meta = DONE / md_file.name
        shutil.move(str(md_file), dest_meta)
        if companion and companion.exists():
            shutil.move(str(companion), DONE / companion.name)

        _update_frontmatter(dest_meta, {
            "status": "done",
            "approval_status": "approved",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })
        log_action("file_approved", str(dest_meta))
        logger.info("Approved file completed: %s", dest_meta.name)
        count += 1

    return count


def process_rejected_files() -> int:
    """Check Rejected/ for files that were rejected by a human.

    Moves rejected files to Done/ with rejected status.
    Returns count of files processed.
    """
    REJECTED.mkdir(parents=True, exist_ok=True)
    count = 0

    for md_file in sorted(REJECTED.glob("FILE_*.md")):
        companion = _find_companion(md_file, REJECTED)

        dest_meta = DONE / md_file.name
        shutil.move(str(md_file), dest_meta)
        if companion and companion.exists():
            shutil.move(str(companion), DONE / companion.name)

        _update_frontmatter(dest_meta, {
            "status": "done",
            "approval_status": "rejected",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        })
        log_action("file_rejected", str(dest_meta))
        logger.info("Rejected file archived: %s", dest_meta.name)
        count += 1

    return count


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_cycle() -> int:
    """Process one batch of pending files. Returns number processed."""
    pending = sorted(
        NEEDS_ACTION.glob("FILE_*.md"),
        key=lambda p: p.stat().st_mtime,
    )

    # Filter to only status: pending
    actionable = []
    for p in pending:
        fm = _read_frontmatter(p)
        if fm.get("status") == "pending":
            actionable.append(p)
        if len(actionable) >= MAX_BATCH_SIZE:
            break

    if not actionable:
        return 0

    logger.info("Processing %d file(s) this cycle", len(actionable))
    processed = 0

    for meta_path in actionable:
        # Claim
        in_prog_meta, in_prog_companion = claim_file(meta_path)

        # Create Plan.md if warranted (S4)
        fm = _read_frontmatter(in_prog_meta)
        if should_create_plan(fm):
            create_plan(in_prog_meta, fm)

        # Process
        success = process_file(in_prog_meta, in_prog_companion)

        if success:
            # Check HITL before completing (S6)
            if evaluate_hitl(in_prog_meta):
                route_to_approval(in_prog_meta, in_prog_companion)
                logger.info("File requires approval: %s", in_prog_meta.name)
            else:
                move_to_done(in_prog_meta, in_prog_companion)
            processed += 1
        else:
            handle_failure(in_prog_meta, in_prog_companion)

    # Process any approved/rejected files from Pending_Approval
    approved_count = process_approved_files()
    rejected_count = process_rejected_files()
    processed += approved_count

    # Update dashboard after processing
    if processed > 0 or approved_count > 0 or rejected_count > 0:
        update_dashboard()

    return processed


def main() -> None:
    """Start the orchestrator loop."""
    parser = argparse.ArgumentParser(description="Zoya Orchestrator")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process one cycle and exit (for cron jobs)",
    )
    args = parser.parse_args()

    if not acquire_lock():
        logger.error(
            "Another orchestrator is already running. Exiting. "
            "If this is wrong, delete %s",
            str(ORCHESTRATOR_LOCK),
        )
        sys.exit(1)

    atexit.register(release_lock)
    logger.info("Orchestrator started (PID %d)%s", os.getpid(), " [--once]" if args.once else "")
    log_action("orchestrator_started", "system")

    try:
        if args.once:
            count = run_cycle()
            logger.info("Single cycle complete: %d file(s) processed", count)
        else:
            while True:
                count = run_cycle()
                if count > 0:
                    logger.info("Cycle complete: %d file(s) processed", count)
                time.sleep(ORCHESTRATOR_POLL_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Orchestrator stopping...")
    finally:
        release_lock()
        log_action("orchestrator_stopped", "system")
        logger.info("Orchestrator stopped.")


if __name__ == "__main__":
    main()
