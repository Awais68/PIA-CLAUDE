---
skill_name: ErrorRecovery
version: 1.0
trigger: Called by any module that makes external API calls or processes payments
inputs: Exception object, component name, optional payload for offline queue
outputs: Retry result OR alert file in /Needs_Action/ OR offline queue entry
approval_required: "yes — auth errors and payment errors always require human review"
max_runtime: 5
---

## Objective

Provide consistent, safe error handling across all Zoya integrations so that
transient failures are auto-healed, auth problems alert the human immediately,
and payment actions NEVER auto-retry without fresh approval.

## Step-by-Step Process

1. **Classify the error** using `classify_error(exc)` — returns one of:
   - `transient` (network blip, timeout)
   - `rate_limit` (HTTP 429)
   - `auth` (401/403, invalid token)
   - `payment` (any payment/invoice action failure)
   - `permanent` (400 bad request)
   - `component` (service entirely down)

2. **Apply the retry policy** for that category:
   | Category   | Max Attempts | Base Delay | Jitter |
   |------------|-------------|------------|--------|
   | transient  | 5           | 2s         | yes    |
   | rate_limit | 4           | 30s        | yes    |
   | auth       | 1 (no retry)| —          | —      |
   | payment    | 1 (no retry)| —          | —      |
   | permanent  | 1 (no retry)| —          | —      |
   | component  | 3           | 10s        | yes    |

3. **Auth error path**: Call `handle_auth_error(component, detail)` which:
   - Creates `ALERT_auth_error_<component>_<timestamp>.md` in `/Needs_Action/`
   - Marks component as paused in `ComponentHealth`
   - Queues future work offline (no data lost)

4. **Payment error path**: Call `_create_payment_error_alert(component, detail)` which:
   - Creates `PAYMENT_ERROR_*.md` in `/Pending_Approval/`
   - Sets `auto_retry: false`
   - Requires explicit human move to `/Approved/` to retry

5. **Component down path**: After 3 failures, apply degradation rule:
   - `queue_to_local` → save to `/Vault/Queue/<component>/`
   - `watchers_continue` → watchers run; queue grows; alert created
   - `log_only` → log and discard

6. **Offline queue replay**: When component recovers, call `flush_offline_queue(component, handler)`

## Success Criteria

- Transient errors resolve within 5 attempts without human intervention
- Auth errors immediately surface in Obsidian for human action
- Payment failures appear in `/Pending_Approval/` with `auto_retry: false`
- No work is lost when components are down (offline queue depth > 0)
- `ComponentHealth.is_healthy(component)` returns True after recovery

## Error Handling

- If `classify_error` itself throws → default to `transient`
- If alert file cannot be written → log to stderr and raise
- If offline queue write fails (disk full) → raise immediately with clear message

## Example Input/Output

**Input (transient):**
```python
safe_call(requests.get, "https://api.twitter.com/...", component="twitter")
# raises ConnectionError on attempt 1
# waits 2s, retries → success on attempt 2
```

**Input (auth error):**
```python
safe_call(client.create_tweet, text="Hello", component="twitter")
# raises tweepy.Unauthorized (401)
# → creates ALERT_auth_error_twitter_20260220_230000.md in Needs_Action/
# → future twitter calls queue to /Vault/Queue/twitter/
```

**Input (payment error):**
```python
safe_call(odoo.pay_invoice, invoice_id=42, component="payment")
# raises PaymentError
# → creates PAYMENT_ERROR_payment_20260220_230000.md in Pending_Approval/
# → NEVER auto-retried
```
