"""Ralph Wiggum Loop — Autonomous Multi-Step Task Completion.

Implements the Stop Hook pattern: Claude is given a task and a "completion
promise" (a string that appears in Claude's output OR a file moving to /Done/).
If Claude exits without satisfying the promise, the loop re-injects the prompt
with previous context until max_iterations is reached.

State is persisted to /Vault/.ralph_state/ so the loop survives restarts.

Usage:
    # Programmatic
    from src.ralph_wiggum import run_ralph_loop
    run_ralph_loop(
        task_prompt="Process the pending invoice and move it to Done",
        completion_promise="moved to Done",
        max_iterations=3,
        watch_path=Path("AI_Employee_Vault/Done/FILE_*.md"),
    )

    # CLI
    uv run python -m src.ralph_wiggum \\
        --prompt "Generate weekly briefing" \\
        --promise "Briefing generated" \\
        --max-iterations 5 \\
        --dry-run

Max iteration guidelines:
    Email processing:   max 5
    Invoice generation: max 3
    Social posting:     max 3
    Weekly audit:       max 10
"""

from __future__ import annotations

import argparse
import glob as _glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import DONE, PROJECT_ROOT, VAULT_PATH
from src.utils import log_action, setup_logger

logger = setup_logger("ralph_wiggum")

RALPH_STATE_DIR = VAULT_PATH / ".ralph_state"

# Max iteration defaults per task type
MAX_ITERATIONS_BY_TYPE: dict[str, int] = {
    "email_processing": 5,
    "invoice_generation": 3,
    "social_media_posting": 3,
    "weekly_audit": 10,
    "default": 5,
}


# ---------------------------------------------------------------------------
# State file management
# ---------------------------------------------------------------------------

def _state_path(task_id: str) -> Path:
    return RALPH_STATE_DIR / f"task_{task_id}.json"


def _save_state(state: dict[str, Any]) -> None:
    RALPH_STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = _state_path(state["task_id"])
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _load_state(task_id: str) -> dict[str, Any] | None:
    path = _state_path(task_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cleanup_state(task_id: str) -> None:
    path = _state_path(task_id)
    if path.exists():
        path.unlink()


def list_active_tasks() -> list[dict[str, Any]]:
    """Return all in-progress Ralph state files."""
    if not RALPH_STATE_DIR.exists():
        return []
    tasks = []
    for f in RALPH_STATE_DIR.glob("task_*.json"):
        try:
            tasks.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return tasks


# ---------------------------------------------------------------------------
# Completion checkers
# ---------------------------------------------------------------------------

def _output_contains_promise(output: str, promise: str) -> bool:
    """Check if Claude's stdout contains the completion promise string."""
    return promise.lower() in output.lower()


def _file_moved_to_done(watch_glob: str | None) -> bool:
    """Check if a file matching watch_glob now exists in /Done/."""
    if not watch_glob:
        return False
    matches = _glob.glob(watch_glob)
    return bool(matches)


def _check_completion(
    output: str,
    completion_promise: str,
    watch_glob: str | None,
) -> bool:
    """Return True if either completion condition is satisfied."""
    if completion_promise and _output_contains_promise(output, completion_promise):
        return True
    if watch_glob and _file_moved_to_done(watch_glob):
        return True
    return False


# ---------------------------------------------------------------------------
# Claude invocation
# ---------------------------------------------------------------------------

def _invoke_claude(prompt: str, dry_run: bool = False) -> tuple[bool, str]:
    """Run claude CLI with the given prompt.

    Returns (success, stdout_output).
    """
    if dry_run:
        logger.info("[DRY RUN] Would invoke Claude with prompt:\n%.200s…", prompt)
        simulated = f"[DRY RUN] Claude response to: {prompt[:100]}\nTask completed successfully."
        return True, simulated

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(PROJECT_ROOT),
            env=env,
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output
    except subprocess.TimeoutExpired:
        return False, "Claude timed out after 180s"
    except FileNotFoundError:
        return False, "Claude Code CLI not found"
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Main Ralph Wiggum loop
# ---------------------------------------------------------------------------

def run_ralph_loop(
    task_prompt: str,
    completion_promise: str = "",
    max_iterations: int | None = None,
    watch_glob: str | None = None,
    task_type: str = "default",
    task_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute a task autonomously, re-trying until done or max_iterations reached.

    Args:
        task_prompt:        The full prompt to give Claude on each iteration.
        completion_promise: String that must appear in Claude's output to count
                            as complete (e.g. "Briefing generated").
        max_iterations:     Override the default for task_type.
        watch_glob:         Glob pattern for a file that should exist in /Done/
                            when the task completes (alternative to promise).
        task_type:          One of the keys in MAX_ITERATIONS_BY_TYPE.
        task_id:            Unique task identifier (auto-generated if None).
        dry_run:            If True, log prompts without actually calling Claude.

    Returns:
        Dict with keys: task_id, status, iterations_used, completed, output.
    """
    now = datetime.now(timezone.utc)
    task_id = task_id or now.strftime("%Y%m%d_%H%M%S_%f")
    max_iters = max_iterations or MAX_ITERATIONS_BY_TYPE.get(task_type, 5)

    # Create initial state
    state: dict[str, Any] = {
        "task_id": task_id,
        "task_prompt": task_prompt,
        "task_type": task_type,
        "max_iterations": max_iters,
        "completion_promise": completion_promise,
        "watch_glob": watch_glob,
        "current_iteration": 0,
        "started_at": now.isoformat(),
        "status": "running",
        "outputs": [],
        "dry_run": dry_run,
    }
    _save_state(state)

    logger.info(
        "Ralph Wiggum loop starting: task=%s type=%s max_iter=%d dry_run=%s",
        task_id, task_type, max_iters, dry_run,
    )
    log_action(
        "ralph_wiggum_started",
        task_id,
        {"task_type": task_type, "max_iterations": max_iters, "dry_run": dry_run},
    )

    completed = False
    final_output = ""
    previous_context = ""

    for iteration in range(1, max_iters + 1):
        state["current_iteration"] = iteration
        _save_state(state)

        # Re-inject previous context on subsequent iterations
        if previous_context:
            injected_prompt = (
                f"{task_prompt}\n\n"
                f"--- Previous attempt context (iteration {iteration - 1}) ---\n"
                f"{previous_context[-2000:]}\n"
                f"--- End of context ---\n\n"
                f"The task is NOT yet complete. Please continue and ensure "
                f"'{completion_promise or 'the task'}' is satisfied before you stop."
            )
        else:
            injected_prompt = task_prompt

        logger.info("Ralph iteration %d/%d for task %s", iteration, max_iters, task_id)

        success, output = _invoke_claude(injected_prompt, dry_run=dry_run)
        state["outputs"].append({
            "iteration": iteration,
            "success": success,
            "output_preview": output[:500],
        })
        previous_context = output
        final_output = output

        # Check completion
        if _check_completion(output, completion_promise, watch_glob):
            completed = True
            logger.info(
                "Ralph task %s COMPLETE after %d iteration(s)", task_id, iteration
            )
            break

        if not success:
            logger.warning("Claude call failed on iteration %d — will retry", iteration)

        if iteration < max_iters:
            logger.info(
                "Task not yet complete. Re-injecting prompt (iteration %d/%d)…",
                iteration + 1, max_iters,
            )
            time.sleep(2)  # brief pause between iterations

    # Finalise
    final_status = "completed" if completed else "max_iterations_reached"
    state["status"] = final_status
    state["completed"] = completed
    state["finished_at"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)

    log_action(
        "ralph_wiggum_completed",
        task_id,
        {
            "task_type": task_type,
            "iterations_used": state["current_iteration"],
            "completed": completed,
            "status": final_status,
        },
        result="success" if completed else "failure",
    )

    if completed:
        logger.info("Ralph loop DONE: %s (%d iterations)", task_id, state["current_iteration"])
        _cleanup_state(task_id)
    else:
        logger.warning(
            "Ralph loop EXHAUSTED: %s — task not confirmed complete after %d iterations",
            task_id, max_iters,
        )
        _create_ralph_exhausted_alert(state, final_output)

    return {
        "task_id": task_id,
        "status": final_status,
        "iterations_used": state["current_iteration"],
        "completed": completed,
        "output": final_output[:2000],
    }


def _create_ralph_exhausted_alert(state: dict, last_output: str) -> None:
    """Create a Needs_Action alert when Ralph exhausts all iterations."""
    from src.config import NEEDS_ACTION

    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    alert_path = NEEDS_ACTION / f"RALPH_EXHAUSTED_{state['task_id']}_{ts}.md"

    alert_path.write_text(
        f"---\n"
        f"type: ralph_exhausted\n"
        f"task_id: {state['task_id']}\n"
        f"task_type: {state['task_type']}\n"
        f"iterations_used: {state['current_iteration']}\n"
        f"max_iterations: {state['max_iterations']}\n"
        f"started_at: {state['started_at']}\n"
        f"severity: warning\n"
        f"status: pending\n"
        f"---\n\n"
        f"# ⚠️ Ralph Wiggum Loop Exhausted\n\n"
        f"Task `{state['task_id']}` ({state['task_type']}) did not complete "
        f"after {state['max_iterations']} iterations.\n\n"
        f"**Completion promise:** `{state.get('completion_promise', 'N/A')}`\n"
        f"**Watch glob:** `{state.get('watch_glob', 'N/A')}`\n\n"
        f"## Last Claude Output (preview)\n\n"
        f"```\n{last_output[:1000]}\n```\n\n"
        f"## Required Action\n\n"
        f"1. Review what Claude attempted above\n"
        f"2. Complete the task manually if needed\n"
        f"3. Move this file to `/Approved/` once resolved\n"
        f"4. Adjust `max_iterations` in `.claude/skills/ralph-wiggum/SKILL.md` "
        f"if this task type consistently needs more iterations\n",
        encoding="utf-8",
    )
    logger.warning("Ralph exhausted alert created: %s", alert_path.name)


# ---------------------------------------------------------------------------
# Orchestrator integration: detect stuck tasks + trigger Ralph loop
# ---------------------------------------------------------------------------

def check_and_trigger_for_stuck(
    in_progress_dir: Path | None = None,
    stuck_threshold_minutes: int = 20,
    dry_run: bool = False,
) -> int:
    """Called from the orchestrator to detect stuck In_Progress items.

    If a file has been In_Progress longer than stuck_threshold_minutes,
    Ralph loop re-attempts the task.

    Args:
        in_progress_dir:         Path to In_Progress/ (defaults to config).
        stuck_threshold_minutes: Age in minutes before a file is "stuck".
        dry_run:                 If True, log but don't invoke Claude.

    Returns:
        Number of stuck tasks re-triggered.
    """
    from src.config import IN_PROGRESS

    ip_dir = in_progress_dir or IN_PROGRESS
    if not ip_dir.exists():
        return 0

    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - (stuck_threshold_minutes * 60)
    triggered = 0

    for md_file in ip_dir.glob("FILE_*.md"):
        mtime = md_file.stat().st_mtime
        if mtime > cutoff:
            continue  # Not stuck yet

        # Skip if we already started a Ralph loop for this file
        existing = list(RALPH_STATE_DIR.glob(f"task_*{md_file.stem}*.json")) if RALPH_STATE_DIR.exists() else []
        if existing:
            continue

        age_minutes = (now.timestamp() - mtime) / 60
        logger.warning(
            "Stuck task detected: %s (%.0f min in In_Progress) — triggering Ralph loop",
            md_file.name, age_minutes,
        )
        log_action(
            "ralph_stuck_trigger",
            str(md_file),
            {"age_minutes": round(age_minutes, 1), "dry_run": dry_run},
        )

        prompt = (
            f"You are Zoya. A task file has been stuck in In_Progress for {age_minutes:.0f} minutes.\n\n"
            f"**Stuck file:** `{md_file}`\n\n"
            f"Please:\n"
            f"1. Read the stuck metadata file\n"
            f"2. Determine what processing was needed\n"
            f"3. Complete the processing using the inbox-processor skill\n"
            f"4. Update the frontmatter status to 'done'\n"
            f"5. Do NOT move files — the orchestrator handles that\n\n"
            f"Confirm completion by writing 'Processing complete' in your response."
        )

        run_ralph_loop(
            task_prompt=prompt,
            completion_promise="Processing complete",
            task_type="default",
            task_id=f"stuck_{md_file.stem}",
            dry_run=dry_run,
        )
        triggered += 1

    return triggered


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum — Autonomous multi-step task completion loop"
    )
    parser.add_argument("--prompt", required=True, help="Task prompt for Claude")
    parser.add_argument(
        "--promise",
        default="",
        help="Completion promise: string that must appear in Claude's output",
    )
    parser.add_argument(
        "--watch-glob",
        default=None,
        help="Glob pattern for a file that should appear in Done/ on completion",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum iterations (overrides task-type default)",
    )
    parser.add_argument(
        "--task-type",
        default="default",
        choices=list(MAX_ITERATIONS_BY_TYPE.keys()),
        help="Task type (sets default max_iterations)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log prompts without calling Claude",
    )
    args = parser.parse_args()

    result = run_ralph_loop(
        task_prompt=args.prompt,
        completion_promise=args.promise,
        max_iterations=args.max_iterations,
        watch_glob=args.watch_glob,
        task_type=args.task_type,
        dry_run=args.dry_run,
    )

    status_symbol = "✅" if result["completed"] else "⚠️"
    print(
        f"{status_symbol} Ralph loop finished: {result['status']} "
        f"({result['iterations_used']} iteration(s))"
    )
    sys.exit(0 if result["completed"] else 1)


if __name__ == "__main__":
    main()
