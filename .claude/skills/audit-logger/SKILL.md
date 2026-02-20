---
skill_name: AuditLogger
version: 1.0
trigger: Called by every module that performs an action (send, post, process, approve)
inputs: action_type, target, actor, parameters, approval_status, result, error
outputs: Appends JSON entry to /Vault/Logs/YYYY-MM-DD.json
approval_required: "no — read-only audit trail"
max_runtime: 1
---

## Objective

Maintain a tamper-evident, structured JSON audit trail of every action Zoya
takes. Enables compliance review, debugging, weekly summaries, and CEO briefing
data aggregation.

## Step-by-Step Process

1. **Log an action** by calling `audit_log(action_type, target, **kwargs)`:
   ```python
   from src.audit_logger import audit_log
   audit_log(
       action_type="email_send",
       target="client@example.com",
       actor="claude_code",
       parameters={"subject": "Invoice #42"},
       approval_status="human_approved",
       approved_by="human",
       result="success",
   )
   ```

2. **Log format** (one JSON object per line in YYYY-MM-DD.json):
   ```json
   {
     "timestamp": "2026-02-20T23:00:00+00:00",
     "action_type": "email_send",
     "actor": "claude_code",
     "target": "client@example.com",
     "parameters": {"subject": "Invoice #42"},
     "approval_status": "human_approved",
     "approved_by": "human",
     "result": "success",
     "error": null
   }
   ```

3. **Weekly summary** (runs automatically Sunday evening via audit_generator):
   - Call `weekly_audit_summary(append_to_dashboard=True)`
   - Appends a `## 📊 Weekly Audit Summary` block to `Dashboard.md`

4. **Log retention** (runs Sunday evening):
   - Call `purge_old_logs(retention_days=90)`
   - Deletes any `*.json` log file older than 90 days

5. **Query logs** for CEO briefing / Ralph checks:
   ```python
   entries = read_logs(days=7, action_type_filter="payment")
   ```

## Success Criteria

- Every external action appears in today's `.json` log within 1s
- Log files persist for exactly 90 days minimum
- Weekly summary appears in `Dashboard.md` every Sunday
- `get_period_stats(days=7)` returns accurate counts for CEO briefing

## Error Handling

- If log directory doesn't exist → create it (`LOGS.mkdir(parents=True)`)
- If log file write fails (disk full) → log to stderr only, never crash caller
- If a log line is malformed JSON on read → skip that line, continue

## Valid `action_type` values

```
file_queued, file_claimed, file_done, file_retry, file_quarantined,
file_routed_to_approval, file_approved, file_rejected,
email_send, email_send_approved, email_send_rejected,
email_received, email_processed,
payment_initiated, payment_approved, payment_rejected,
payment_error, invoice_create, invoice_sent,
social_post, social_post_approved, social_post_rejected,
twitter_post, linkedin_post, facebook_post, instagram_post,
social_metrics_fetched,
whatsapp_received, whatsapp_sent,
contact_created, contact_updated,
orchestrator_started, orchestrator_stopped,
briefing_generated, audit_generated,
auth_error_alert_created, payment_error_alert_created,
component_failure, component_recovered,
ralph_wiggum_started, ralph_wiggum_completed
```

## Example Input/Output

**Input:**
```python
audit_log("twitter_post", "twitter_api", actor="claude_code",
          parameters={"tweet_id": "123", "chars": 240},
          approval_status="human_approved", approved_by="human",
          result="success")
```

**Output** (appended to `/Vault/Logs/2026-02-20.json`):
```json
{"timestamp":"2026-02-20T23:05:00+00:00","action_type":"twitter_post","actor":"claude_code","target":"twitter_api","parameters":{"tweet_id":"123","chars":240},"approval_status":"human_approved","approved_by":"human","result":"success","error":null}
```
