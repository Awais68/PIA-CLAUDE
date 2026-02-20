"""Error Recovery Engine for Zoya — Gold Tier.

Implements all resilience strategies:
  - Exponential backoff for transient errors (network, rate limits)
  - Auth error handling: pause + create ALERT_auth_error.md in Needs_Action/
  - Payment error HITL: NEVER auto-retry; always require fresh approval
  - Component failure degradation:
      Gmail down  → queue to /Vault/Queue/gmail/
      Claude down → watchers continue, queue grows, alert created
      WhatsApp down → log only, no-op
  - Local offline queue at /Vault/Queue/ when external APIs unavailable

Usage:
    from src.error_recovery import with_retry, handle_auth_error
    from src.error_recovery import queue_offline, ComponentHealth
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, TypeVar

from src.config import (
    NEEDS_ACTION,
    PENDING_APPROVAL,
    VAULT_PATH,
)
from src.utils import log_action, setup_logger

logger = setup_logger("error_recovery")

# ---------------------------------------------------------------------------
# Offline queue directory
# ---------------------------------------------------------------------------
QUEUE_DIR = VAULT_PATH / "Queue"

# ---------------------------------------------------------------------------
# Error categories
# ---------------------------------------------------------------------------

class ErrorCategory(str, Enum):
    TRANSIENT = "transient"       # network blip, timeout → retry with backoff
    RATE_LIMIT = "rate_limit"     # 429 → retry after longer delay
    AUTH = "auth"                 # 401/403 → alert human, pause integration
    PAYMENT = "payment"           # payment action → NEVER auto-retry
    PERMANENT = "permanent"       # 400 bad request → no retry
    COMPONENT = "component"       # entire service down → degraded mode

# ---------------------------------------------------------------------------
# Retry config per error category
# ---------------------------------------------------------------------------

RETRY_CONFIG: dict[ErrorCategory, dict] = {
    ErrorCategory.TRANSIENT: {
        "max_attempts": 5,
        "base_delay": 2.0,
        "max_delay": 60.0,
        "jitter": True,
    },
    ErrorCategory.RATE_LIMIT: {
        "max_attempts": 4,
        "base_delay": 30.0,
        "max_delay": 300.0,
        "jitter": True,
    },
    ErrorCategory.AUTH: {
        "max_attempts": 1,   # never retry — alert immediately
        "base_delay": 0.0,
        "max_delay": 0.0,
        "jitter": False,
    },
    ErrorCategory.PAYMENT: {
        "max_attempts": 1,   # never retry — fresh approval required
        "base_delay": 0.0,
        "max_delay": 0.0,
        "jitter": False,
    },
    ErrorCategory.PERMANENT: {
        "max_attempts": 1,
        "base_delay": 0.0,
        "max_delay": 0.0,
        "jitter": False,
    },
    ErrorCategory.COMPONENT: {
        "max_attempts": 3,
        "base_delay": 10.0,
        "max_delay": 120.0,
        "jitter": True,
    },
}


# ---------------------------------------------------------------------------
# Exception classification
# ---------------------------------------------------------------------------

def classify_error(exc: Exception) -> ErrorCategory:
    """Classify an exception into an ErrorCategory.

    Checks exception message and type for known patterns.
    """
    msg = str(exc).lower()

    # Auth patterns
    if any(kw in msg for kw in ("401", "403", "unauthorized", "forbidden",
                                 "invalid credentials", "token expired",
                                 "authenticationerror")):
        return ErrorCategory.AUTH

    # Rate limit patterns
    if any(kw in msg for kw in ("429", "rate limit", "too many requests",
                                 "ratelimit", "quota exceeded")):
        return ErrorCategory.RATE_LIMIT

    # Payment patterns (never auto-retry)
    if any(kw in msg for kw in ("payment", "invoice", "charge", "debit",
                                 "transfer", "transaction failed")):
        return ErrorCategory.PAYMENT

    # Permanent / bad request
    if any(kw in msg for kw in ("400", "bad request", "invalid parameter",
                                 "schema", "validation error")):
        return ErrorCategory.PERMANENT

    # Service/component down
    if any(kw in msg for kw in ("503", "service unavailable", "connection refused",
                                 "connection reset", "no route to host",
                                 "name or service not known", "eof occurred")):
        return ErrorCategory.COMPONENT

    # Default: transient
    return ErrorCategory.TRANSIENT


# ---------------------------------------------------------------------------
# Exponential backoff decorator / context manager
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    func: Callable,
    *args,
    category: ErrorCategory | None = None,
    component: str = "unknown",
    **kwargs,
) -> Any:
    """Execute func with exponential backoff.

    Args:
        func:      The callable to execute.
        *args:     Positional arguments for func.
        category:  Force a specific error category (auto-detected if None).
        component: Name of the service/component for logging.
        **kwargs:  Keyword arguments for func.

    Returns:
        The return value of func on success.

    Raises:
        The last exception if all retries are exhausted.
        RuntimeError for PAYMENT errors (always re-raises immediately).
    """
    last_exc: Exception | None = None

    for attempt in range(1, 10):  # safety ceiling
        try:
            return func(*args, **kwargs)

        except Exception as exc:
            cat = category or classify_error(exc)
            cfg = RETRY_CONFIG[cat]
            max_attempts = cfg["max_attempts"]

            logger.warning(
                "[%s] Attempt %d/%d failed — category=%s: %s",
                component, attempt, max_attempts, cat.value, exc,
            )
            log_action(
                "error_recovery_attempt",
                component,
                {"attempt": attempt, "category": cat.value, "error": str(exc)[:200]},
                result="failure",
            )

            # Payment errors: NEVER auto-retry — require fresh human approval
            if cat == ErrorCategory.PAYMENT:
                _create_payment_error_alert(component, str(exc))
                raise RuntimeError(
                    f"Payment action failed for {component} — "
                    "fresh human approval required. "
                    f"See Pending_Approval/ for details. Original: {exc}"
                ) from exc

            # Auth errors: alert immediately, no retry
            if cat == ErrorCategory.AUTH:
                handle_auth_error(component, str(exc))
                raise RuntimeError(
                    f"Auth failure for {component} — integration paused. "
                    f"See Needs_Action/ALERT_auth_error_*.md. Original: {exc}"
                ) from exc

            if attempt >= max_attempts:
                last_exc = exc
                break

            # Compute backoff delay
            delay = min(
                cfg["base_delay"] * (2 ** (attempt - 1)),
                cfg["max_delay"],
            )
            if cfg["jitter"]:
                delay = delay * (0.5 + random.random() * 0.5)

            logger.info(
                "[%s] Retrying in %.1fs (attempt %d/%d, category=%s)…",
                component, delay, attempt + 1, max_attempts, cat.value,
            )
            time.sleep(delay)

    raise last_exc or RuntimeError(f"All retries exhausted for {component}")


# ---------------------------------------------------------------------------
# Auth error handler
# ---------------------------------------------------------------------------

def handle_auth_error(component: str, error_detail: str = "") -> Path:
    """Create an ALERT_auth_error_*.md in Needs_Action/ and pause the component.

    Args:
        component:    Name of the failing integration (e.g. "gmail", "twitter").
        error_detail: The raw error message for context.

    Returns:
        Path to the created alert file.
    """
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    safe_comp = "".join(c if c.isalnum() else "_" for c in component)[:30]
    alert_path = NEEDS_ACTION / f"ALERT_auth_error_{safe_comp}_{ts}.md"

    alert_path.write_text(
        f"---\n"
        f"type: auth_error_alert\n"
        f"component: {component}\n"
        f"severity: critical\n"
        f"status: pending\n"
        f"created_at: {now.isoformat()}\n"
        f"requires_human: true\n"
        f"---\n\n"
        f"# 🔐 Authentication Error — {component.upper()}\n\n"
        f"**Component:** {component}  \n"
        f"**Time:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}  \n"
        f"**Severity:** CRITICAL — integration is paused\n\n"
        f"## Error Detail\n\n"
        f"```\n{error_detail[:1000]}\n```\n\n"
        f"## Required Action\n\n"
        f"1. Check `.env` for `{component.upper()}_API_KEY` / credentials\n"
        f"2. Verify credentials haven't expired in the service dashboard\n"
        f"3. Re-run auth flow if needed (see setup docs)\n"
        f"4. Move this file to `/Approved/` once credentials are fixed\n"
        f"5. Restart the affected watcher/integration\n\n"
        f"## Impact While Paused\n\n"
        f"- Items that would use `{component}` are being queued locally\n"
        f"- No data is lost — queue at `/Vault/Queue/{component}/`\n"
        f"- All other integrations continue normally\n",
        encoding="utf-8",
    )

    logger.critical("Auth error — %s integration PAUSED. Alert: %s", component, alert_path.name)
    log_action(
        "auth_error_alert_created",
        str(alert_path),
        {"component": component, "error": error_detail[:200]},
        result="failure",
    )
    return alert_path


# ---------------------------------------------------------------------------
# Payment error handler
# ---------------------------------------------------------------------------

def _create_payment_error_alert(component: str, error_detail: str) -> Path:
    """Create a payment failure alert in Pending_Approval/ requiring fresh approval."""
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    safe_comp = "".join(c if c.isalnum() else "_" for c in component)[:30]
    alert_path = PENDING_APPROVAL / f"PAYMENT_ERROR_{safe_comp}_{ts}.md"

    alert_path.write_text(
        f"---\n"
        f"type: payment_error\n"
        f"component: {component}\n"
        f"severity: critical\n"
        f"status: pending_approval\n"
        f"created_at: {now.isoformat()}\n"
        f"approval_required: true\n"
        f"auto_retry: false\n"
        f"---\n\n"
        f"# 💳 Payment Action Failed — Fresh Approval Required\n\n"
        f"**Component:** {component}  \n"
        f"**Time:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}  \n"
        f"**Auto-retry:** DISABLED (payment actions require fresh human approval)\n\n"
        f"## Error Detail\n\n"
        f"```\n{error_detail[:1000]}\n```\n\n"
        f"## Required Action\n\n"
        f"1. Review the payment details above\n"
        f"2. Verify the payment method and destination are correct\n"
        f"3. If you want to retry, move this file to `/Approved/`\n"
        f"4. If you want to cancel, move to `/Rejected/`\n\n"
        f"> ⚠️ **NEVER** auto-retried. Every payment attempt requires explicit human approval.\n",
        encoding="utf-8",
    )

    logger.critical("Payment error — %s. Alert at %s", component, alert_path.name)
    log_action(
        "payment_error_alert_created",
        str(alert_path),
        {"component": component},
        result="failure",
    )
    return alert_path


# ---------------------------------------------------------------------------
# Component health tracker
# ---------------------------------------------------------------------------

class ComponentHealth:
    """Tracks liveness of individual integrations.

    Supports degraded mode: when a component is marked down, callers
    can route work to the offline queue instead of failing.
    """

    _status: dict[str, dict] = {}  # class-level shared state

    DEGRADATION_RULES: dict[str, str] = {
        "gmail":     "queue_to_local",   # queue incoming gmail items locally
        "claude":    "watchers_continue", # watchers run, queue grows, alert created
        "whatsapp":  "log_only",          # log failed sends, no retry
        "twitter":   "queue_to_local",
        "linkedin":  "queue_to_local",
        "odoo":      "queue_to_local",
    }

    @classmethod
    def mark_healthy(cls, component: str) -> None:
        was_down = cls._status.get(component, {}).get("status") == "down"
        cls._status[component] = {
            "status": "healthy",
            "last_healthy": datetime.now(timezone.utc).isoformat(),
            "consecutive_failures": 0,
        }
        if was_down:
            logger.info("[%s] Component recovered — resuming normal operation", component)
            log_action("component_recovered", component)

    @classmethod
    def mark_failure(cls, component: str, exc: Exception) -> None:
        current = cls._status.get(component, {"consecutive_failures": 0})
        failures = current.get("consecutive_failures", 0) + 1
        cls._status[component] = {
            "status": "down" if failures >= 3 else "degraded",
            "last_failure": datetime.now(timezone.utc).isoformat(),
            "consecutive_failures": failures,
            "last_error": str(exc)[:200],
        }

        level = "down" if failures >= 3 else "degraded"
        logger.error(
            "[%s] Component %s (failures=%d): %s",
            component, level, failures, exc,
        )
        log_action(
            "component_failure",
            component,
            {"failures": failures, "level": level, "error": str(exc)[:200]},
            result="failure",
        )

        if failures == 3:
            _create_component_alert(component, str(exc))

    @classmethod
    def is_healthy(cls, component: str) -> bool:
        return cls._status.get(component, {}).get("status", "healthy") == "healthy"

    @classmethod
    def get_degradation_rule(cls, component: str) -> str:
        return cls.DEGRADATION_RULES.get(component, "log_only")

    @classmethod
    def status_summary(cls) -> dict[str, dict]:
        return dict(cls._status)


def _create_component_alert(component: str, error: str) -> None:
    """Create a Needs_Action alert when a component hits 3 consecutive failures."""
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    safe = "".join(c if c.isalnum() else "_" for c in component)[:30]
    alert = NEEDS_ACTION / f"ALERT_component_down_{safe}_{ts}.md"

    rule = ComponentHealth.DEGRADATION_RULES.get(component, "log_only")
    alert.write_text(
        f"---\n"
        f"type: component_alert\n"
        f"component: {component}\n"
        f"severity: critical\n"
        f"status: pending\n"
        f"created_at: {now.isoformat()}\n"
        f"degradation_rule: {rule}\n"
        f"---\n\n"
        f"# 🔴 Component Down: {component.upper()}\n\n"
        f"After 3 consecutive failures, `{component}` is marked as DOWN.\n\n"
        f"**Degradation mode:** `{rule}`\n\n"
        f"## What's happening\n\n"
        f"- **gmail/twitter/linkedin/odoo:** items queued at `/Vault/Queue/{component}/`\n"
        f"- **claude:** watchers continue, queue grows; alert you when Claude recovers\n"
        f"- **whatsapp:** failed sends are logged only\n\n"
        f"## Last Error\n\n"
        f"```\n{error[:500]}\n```\n\n"
        f"## Resolution\n\n"
        f"1. Investigate the error above\n"
        f"2. Fix the underlying issue\n"
        f"3. Move this file to `/Approved/` to clear the alert\n"
        f"4. The component will automatically recover on next successful call\n",
        encoding="utf-8",
    )
    logger.critical("Component DOWN alert created for %s", component)


# ---------------------------------------------------------------------------
# Offline local queue
# ---------------------------------------------------------------------------

def queue_offline(component: str, payload: dict) -> Path:
    """Save a work item to the local offline queue for a component.

    Used when a component is unavailable (auth error, service down).
    Items are persisted to /Vault/Queue/<component>/ as JSON files.

    Args:
        component: The target integration (e.g. "gmail", "twitter").
        payload:   Arbitrary dict describing the work to be done later.

    Returns:
        Path to the queued JSON file.
    """
    queue_path = QUEUE_DIR / component
    queue_path.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S_%f")
    item_file = queue_path / f"QUEUED_{ts}.json"

    item = {
        "queued_at": now.isoformat(),
        "component": component,
        "payload": payload,
        "status": "queued",
        "retry_count": 0,
    }
    item_file.write_text(json.dumps(item, indent=2), encoding="utf-8")
    logger.info("Queued offline item for %s: %s", component, item_file.name)
    log_action("offline_queued", str(item_file), {"component": component})
    return item_file


def flush_offline_queue(
    component: str,
    handler: Callable[[dict], bool],
) -> tuple[int, int]:
    """Attempt to replay queued items for a component.

    Args:
        component: The integration to flush.
        handler:   Callable that takes a payload dict and returns True on success.

    Returns:
        (success_count, failure_count)
    """
    queue_path = QUEUE_DIR / component
    if not queue_path.exists():
        return 0, 0

    success = failure = 0
    for item_file in sorted(queue_path.glob("QUEUED_*.json")):
        try:
            item = json.loads(item_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        try:
            ok = handler(item["payload"])
            if ok:
                item_file.unlink()
                success += 1
                log_action("offline_flushed", str(item_file), {"component": component})
            else:
                failure += 1
        except Exception as exc:
            failure += 1
            logger.warning("Failed to flush %s: %s", item_file.name, exc)

    logger.info("Flushed offline queue for %s: %d ok, %d failed", component, success, failure)
    return success, failure


def get_queue_depth(component: str | None = None) -> dict[str, int]:
    """Return count of queued items per component (or all if component=None)."""
    if not QUEUE_DIR.exists():
        return {}

    if component:
        q = QUEUE_DIR / component
        return {component: len(list(q.glob("QUEUED_*.json"))) if q.exists() else 0}

    result = {}
    for subdir in QUEUE_DIR.iterdir():
        if subdir.is_dir():
            result[subdir.name] = len(list(subdir.glob("QUEUED_*.json")))
    return result


# ---------------------------------------------------------------------------
# Convenience: safe_call
# ---------------------------------------------------------------------------

def safe_call(
    func: Callable,
    *args,
    component: str = "unknown",
    fallback_queue_payload: dict | None = None,
    **kwargs,
) -> Any | None:
    """Call func with retry + component health tracking + optional offline queue.

    On failure:
    - Updates ComponentHealth.
    - If fallback_queue_payload is provided, queues to offline queue.
    - Returns None instead of raising.

    Usage:
        result = safe_call(send_tweet, content, component="twitter",
                           fallback_queue_payload={"content": content})
    """
    try:
        result = with_retry(func, *args, component=component, **kwargs)
        ComponentHealth.mark_healthy(component)
        return result
    except Exception as exc:
        ComponentHealth.mark_failure(component, exc)

        if fallback_queue_payload is not None:
            rule = ComponentHealth.get_degradation_rule(component)
            if rule == "queue_to_local":
                queue_offline(component, fallback_queue_payload)
            elif rule == "log_only":
                logger.warning("[%s] log_only mode — item dropped: %s", component, exc)
            # claude → watchers_continue: caller handles this

        return None
