# Enable Automation in Orchestrator - Step-by-Step Guide

**Time Required**: 5 minutes
**Difficulty**: Easy (copy-paste)
**File to Edit**: `src/orchestrator.py`

---

## Overview

The automation processors are ready but not yet wired into the main orchestrator. This guide shows exactly what code to add and where.

---

## Step 1: Open the Orchestrator File

```bash
cd /path/to/vault-control
vim ../src/orchestrator.py
# or use your favorite editor
```

---

## Step 2: Find the `process_file()` Function

Look for this function around **line 422**:

```python
def process_file(meta_path: Path, companion: Path | None) -> bool:
    """Process a file using the configured AI provider.

    Returns True on success, False on failure.
    """
    if AI_PROVIDER == "ollama":
        return _process_with_ollama(meta_path, companion)
    if AI_PROVIDER == "qwen":
        return _process_with_qwen(meta_path, companion)
    return _process_with_claude(meta_path, companion)
```

---

## Step 3: Replace with New Logic

Replace the entire `process_file()` function with this:

```python
def process_file(meta_path: Path, companion: Path | None) -> bool:
    """Process a file using the configured AI provider or automation processors.

    Returns True on success, False on failure.
    """
    # Check if this is an automation task (NEW)
    fm = _read_frontmatter(meta_path)
    file_type = fm.get("type", "").lower()

    # Route automation tasks first (NEW)
    if file_type == "linkedin_automation":
        try:
            from src.cloud_agent.processors.linkedin_automation_processor import process_linkedin_task
            logger.info(f"Processing LinkedIn automation task: {meta_path.name}")
            return process_linkedin_task(meta_path)
        except Exception as e:
            logger.error(f"LinkedIn automation error: {e}", exc_info=True)
            return False

    if file_type == "whatsapp_automation":
        try:
            from src.cloud_agent.processors.whatsapp_automation_processor import process_whatsapp_task
            logger.info(f"Processing WhatsApp automation task: {meta_path.name}")
            return process_whatsapp_task(meta_path)
        except Exception as e:
            logger.error(f"WhatsApp automation error: {e}", exc_info=True)
            return False

    if file_type == "gmail_automation":
        try:
            from src.cloud_agent.processors.gmail_automation_processor import process_gmail_task
            logger.info(f"Processing Gmail automation task: {meta_path.name}")
            return process_gmail_task(meta_path)
        except Exception as e:
            logger.error(f"Gmail automation error: {e}", exc_info=True)
            return False

    # Original AI provider routing (for non-automation tasks)
    if AI_PROVIDER == "ollama":
        return _process_with_ollama(meta_path, companion)
    if AI_PROVIDER == "qwen":
        return _process_with_qwen(meta_path, companion)
    return _process_with_claude(meta_path, companion)
```

---

## Step 4: Save and Verify

1. Save the file (`Esc :wq` in vim)
2. Verify no syntax errors:

```bash
python3 -m py_compile src/orchestrator.py
# Should output nothing if no errors
```

3. Check it imports correctly:

```bash
python3 << 'EOF'
from src.orchestrator import process_file
print("✅ Import successful")
EOF
```

---

## Step 5: Test with Automation Task

Create a test task file:

```bash
cat > AI_Employee_Vault/Needs_Action/AUTOMATION_TEST_001.md << 'EOF'
---
type: linkedin_automation
task_type: post
source: linkedin
status: pending
priority: low
original_name: test_post.md
queued_at: 2026-03-07T12:00:00Z
---

## Post Content
Testing LinkedIn automation integration! 🎉

## Image Path
EOF

echo "✅ Test file created"
```

---

## Step 6: Run Orchestrator

```bash
cd /path/to/vault-control/..
python src/orchestrator.py
```

Expected output:
```
2026-03-07 12:30:45 - orchestrator - INFO - Processing LinkedIn automation task: AUTOMATION_TEST_001.md
2026-03-07 12:30:48 - linkedin_automation - INFO - ✅ Posted to LinkedIn feed: Testing LinkedIn automation...
2026-03-07 12:30:48 - orchestrator - INFO - Moved to Done: AUTOMATION_TEST_001.md
```

---

## Step 7: Verify Success

Check if task was processed:

```bash
# Task should be in Done folder
ls -lh AI_Employee_Vault/Done/AUTOMATION_TEST_001.md

# Check the metadata was updated
cat AI_Employee_Vault/Done/AUTOMATION_TEST_001.md
# Should show: status: done
```

---

## If Something Goes Wrong

### Import Error
```
ModuleNotFoundError: No module named 'src.cloud_agent.processors...'
```
**Fix**: Make sure the processor files exist:
```bash
ls -la src/cloud_agent/processors/
# Should show: linkedin_automation_processor.py, etc.
```

### Process Error
```
LinkedIn automation error: LinkedIn not authenticated
```
**Fix**: Check environment variables:
```bash
echo $LINKEDIN_EMAIL
echo $LINKEDIN_PASSWORD
# Both should be set
```

### File Not Moving
```
Task stays in Needs_Action/
```
**Fix**: Check orchestrator.py syntax:
```bash
python3 -m py_compile src/orchestrator.py
```

---

## Verify Each Processor

Test all three processors individually before running full orchestrator:

### Test LinkedIn
```python
from pathlib import Path
from src.cloud_agent.processors.linkedin_automation_processor import process_linkedin_task

path = Path("AI_Employee_Vault/Needs_Action/TEST_LINKEDIN.md")
result = process_linkedin_task(path)
print(f"LinkedIn Test: {'✅ PASS' if result else '❌ FAIL'}")
```

### Test WhatsApp
```python
from pathlib import Path
from src.cloud_agent.processors.whatsapp_automation_processor import process_whatsapp_task

path = Path("AI_Employee_Vault/Needs_Action/TEST_WHATSAPP.md")
result = process_whatsapp_task(path)
print(f"WhatsApp Test: {'✅ PASS' if result else '❌ FAIL'}")
```

### Test Gmail
```python
from pathlib import Path
from src.cloud_agent.processors.gmail_automation_processor import process_gmail_task

path = Path("AI_Employee_Vault/Needs_Action/TEST_GMAIL.md")
result = process_gmail_task(path)
print(f"Gmail Test: {'✅ PASS' if result else '❌ FAIL'}")
```

---

## Quick Syntax Reference

### Complete Function (Copy-Paste Ready)

```python
def process_file(meta_path: Path, companion: Path | None) -> bool:
    """Process a file using the configured AI provider or automation processors."""
    fm = _read_frontmatter(meta_path)
    file_type = fm.get("type", "").lower()

    if file_type == "linkedin_automation":
        try:
            from src.cloud_agent.processors.linkedin_automation_processor import process_linkedin_task
            logger.info(f"Processing LinkedIn automation task: {meta_path.name}")
            return process_linkedin_task(meta_path)
        except Exception as e:
            logger.error(f"LinkedIn automation error: {e}", exc_info=True)
            return False

    if file_type == "whatsapp_automation":
        try:
            from src.cloud_agent.processors.whatsapp_automation_processor import process_whatsapp_task
            logger.info(f"Processing WhatsApp automation task: {meta_path.name}")
            return process_whatsapp_task(meta_path)
        except Exception as e:
            logger.error(f"WhatsApp automation error: {e}", exc_info=True)
            return False

    if file_type == "gmail_automation":
        try:
            from src.cloud_agent.processors.gmail_automation_processor import process_gmail_task
            logger.info(f"Processing Gmail automation task: {meta_path.name}")
            return process_gmail_task(meta_path)
        except Exception as e:
            logger.error(f"Gmail automation error: {e}", exc_info=True)
            return False

    if AI_PROVIDER == "ollama":
        return _process_with_ollama(meta_path, companion)
    if AI_PROVIDER == "qwen":
        return _process_with_qwen(meta_path, companion)
    return _process_with_claude(meta_path, companion)
```

---

## What This Does

1. **Reads file metadata** - Gets the `type` field from frontmatter
2. **Checks for automation** - If type is `linkedin_automation`, `whatsapp_automation`, or `gmail_automation`
3. **Routes to processor** - Calls the appropriate processor function
4. **Handles errors** - Catches exceptions and logs them
5. **Falls back to AI** - For non-automation files, uses existing AI provider logic

---

## Backward Compatibility

✅ This change is **fully backward compatible**:
- Existing files (invoices, contracts, etc.) still work
- They'll use the existing AI provider logic (Claude/Qwen/Ollama)
- Only files with `type: *_automation` are routed to new processors

---

## What's Next

After enabling automation:

1. **Monitor logs**: `tail -f orchestrator.log | grep automation`
2. **Create tasks**: Add task files to `Needs_Action/`
3. **Watch them run**: Tasks move from `Needs_Action/` → `Done/`
4. **Scale up**: Deploy to cloud VM with PM2

---

## Files to Check

Before and after integration:

**Before** (Current):
```
orchestrator.py → Only handles file_drop and email documents
```

**After** (With Integration):
```
orchestrator.py → Handles:
  ├─ linkedin_automation tasks
  ├─ whatsapp_automation tasks
  ├─ gmail_automation tasks
  └─ file_drop/email tasks (existing)
```

---

## Integration Complete When

✅ `process_file()` function updated
✅ Syntax check passes: `python3 -m py_compile src/orchestrator.py`
✅ Import test passes: Can import all three processors
✅ Test task created and processed
✅ Task appears in `Done/` folder with updated metadata

---

## Rollback Instructions

If you need to revert:

```bash
# Restore original process_file() function
# Find the git diff
git diff src/orchestrator.py

# Revert the file
git checkout src/orchestrator.py
```

---

**Status**: Ready to Enable
**Estimated Time**: 5 minutes
**Difficulty**: Easy (copy-paste)
**Risk Level**: Low (backward compatible)

Next step: Follow steps 1-7 above to enable automation in your orchestrator.
