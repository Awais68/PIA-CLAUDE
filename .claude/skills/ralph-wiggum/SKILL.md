---
skill_name: RalphWiggum
version: 1.0
trigger: "1) Orchestrator detects a task stuck in In_Progress > 20 min; 2) Manual invocation for complex multi-step tasks; 3) Any task with approval_required=true that hasn't moved in expected time"
inputs: task_prompt, completion_promise (string OR watch_glob), max_iterations, task_type
outputs: Task completed (file moved to Done/) OR RALPH_EXHAUSTED alert in Needs_Action/
approval_required: "no — Ralph loop itself is autonomous; it only creates alerts if it fails"
max_runtime: 30
---

## Objective

The Ralph Wiggum Loop implements the **Stop Hook pattern**: give Claude a task
with a completion promise, and keep re-injecting the prompt (with previous
output as context) until Claude satisfies the promise or reaches max_iterations.

Use Ralph when:
- A task requires multiple sequential Claude calls (e.g. process → plan → approve → post)
- A file has been stuck in `/In_Progress/` longer than expected
- A complex pipeline step needs autonomous retry without human intervention

Do NOT use Ralph for:
- Simple single-step tasks (just call the skill directly)
- Payment actions (always require human — never loop payment approvals)
- Tasks that have already been through 3+ failed orchestrator retries (quarantine instead)

## Step-by-Step Process

1. **Create state file** at `/Vault/.ralph_state/task_<TIMESTAMP>.json`:
   ```json
   {
     "task_id": "20260220_230000_123456",
     "task_prompt": "...",
     "task_type": "email_processing",
     "max_iterations": 5,
     "completion_promise": "moved to Done",
     "watch_glob": "AI_Employee_Vault/Done/FILE_*invoice*.md",
     "current_iteration": 0,
     "started_at": "2026-02-20T23:00:00Z",
     "status": "running",
     "outputs": []
   }
   ```

2. **Execute Claude** with the task prompt via `claude --print --dangerously-skip-permissions`

3. **Check completion** after Claude exits:
   - **Promise check:** does stdout contain `completion_promise` string?
   - **File check:** does `watch_glob` match any files in `/Done/`?
   - If EITHER is true → task complete → cleanup state → log success

4. **If NOT complete** AND `current_iteration < max_iterations`:
   - Append previous output as context to the prompt
   - Re-inject: `"The task is NOT yet complete. Please continue and ensure '<promise>' is satisfied."`
   - Sleep 2s, increment iteration counter, go to step 2

5. **If max_iterations reached** without completion:
   - Create `RALPH_EXHAUSTED_<task_id>_<timestamp>.md` in `/Needs_Action/`
   - Log with `result: failure`
   - Keep state file for post-mortem

6. **Orchestrator integration** (`check_and_trigger_for_stuck`):
   - Called every orchestrator cycle
   - Finds files in `/In_Progress/` older than 20 minutes
   - Automatically starts a Ralph loop to rescue them
   - Skips if a Ralph loop is already running for that file

## Completion Strategies

### Strategy A: Promise-based (preferred)
Claude's output must contain a specific string:
```python
run_ralph_loop(
    task_prompt="Process the invoice and write 'Processing complete' when done",
    completion_promise="Processing complete",
    task_type="invoice_generation",
)
```

### Strategy B: File-movement
A file must appear in `/Done/` matching a glob:
```python
run_ralph_loop(
    task_prompt="Generate the weekly briefing",
    watch_glob="AI_Employee_Vault/Briefings/CEO_BRIEFING_*.md",
    task_type="weekly_audit",
)
```

### Strategy C: Combined (most reliable)
Use both — whichever fires first counts as completion.

## Max Iteration Guidelines

| Task Type            | Max Iterations | Rationale                                    |
|----------------------|---------------|----------------------------------------------|
| `email_processing`   | 5             | May need to read, categorize, then reply     |
| `invoice_generation` | 3             | Generate → review → save (3 steps max)       |
| `social_media_posting`| 3            | Draft → approval file → confirm created      |
| `weekly_audit`       | 10            | Complex multi-source aggregation             |
| `default`            | 5             | General purpose fallback                     |

## Success Criteria

- Task completes within max_iterations with `status: completed`
- State file is cleaned up on success
- On failure: `RALPH_EXHAUSTED_*.md` appears in `/Needs_Action/` within 1 minute
- Orchestrator integration catches stuck files within one poll cycle (30s)

## Error Handling

- Claude CLI not found → log error, mark task failed, create alert
- Claude times out (180s) → count as one failed iteration, continue loop
- State file cannot be written → log to stderr, continue without persistence
- Max iterations reached → create exhausted alert, preserve last output for context

## Example: Rescuing a Stuck Invoice

**Scenario:** `FILE_20260220_120000_invoice.md` has been In_Progress for 25 minutes.

**Auto-triggered by orchestrator:**
```python
run_ralph_loop(
    task_prompt="A task file has been stuck in In_Progress for 25 minutes...\n[file content]",
    completion_promise="Processing complete",
    task_type="invoice_generation",
    task_id="stuck_FILE_20260220_120000_invoice",
)
```

**Iteration 1:** Claude reads file, processes it, writes summary → output contains "Processing complete"
**Result:** Completed after 1 iteration ✅

**If Claude fails:** Iteration 2 re-injects with context → Claude retries
**After 3 failures:** `RALPH_EXHAUSTED_stuck_FILE_20260220_120000_invoice.md` in Needs_Action → human reviews

## CLI Usage

```bash
# Rescue a stuck task
uv run python -m src.ralph_wiggum \
    --prompt "Process the invoice at In_Progress/FILE_20260220.md" \
    --promise "Processing complete" \
    --task-type invoice_generation \
    --max-iterations 3

# Dry run (no Claude calls)
uv run python -m src.ralph_wiggum \
    --prompt "Generate weekly briefing" \
    --promise "Briefing generated" \
    --task-type weekly_audit \
    --dry-run
```
