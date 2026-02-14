# Silver Tier Execution Plan - Week by Week

**Generated:** 2026-02-15
**Total Estimated Time:** 26-34 hours across 4-5 weeks
**Assumption:** ~6-8 hours/week available for development

---

## Week 1: Foundation + Quick Wins (6-8h)

**Focus:** Set up all infrastructure, implement zero-dependency features, start long-lead items.

### Day 1 (3-4h) — Infrastructure
- [x] Review blueprint and create execution plan *(this document)*
- [ ] Apply for LinkedIn Developer API access (10 min) — **DO THIS FIRST, approval takes days**
  - URL: https://www.linkedin.com/developers/apps
  - Request `w_member_social` scope
- [ ] Create Silver vault folders (15 min)
  ```bash
  mkdir -p AI_Employee_Vault/{Plans,Pending_Approval,Approved,Rejected,Briefings}
  touch AI_Employee_Vault/{Plans,Pending_Approval,Approved,Rejected,Briefings}/.gitkeep
  ```
- [ ] Update `src/config.py` with Silver paths and settings (30 min)
  - Add: PLANS, PENDING_APPROVAL, APPROVED, REJECTED, BRIEFINGS
  - Add: GMAIL_POLL_INTERVAL, GMAIL_CREDENTIALS, GMAIL_TOKEN
  - Add: HITL_AMOUNT_THRESHOLD, HITL_DEADLINE_DAYS
  - Add: LINKEDIN_DRY_RUN
- [ ] Update `tests/test_config.py` with new path tests (20 min)
- [ ] Create all 6 SKILL.md stubs (30 min) — S8
  - .claude/skills/plan-creator/SKILL.md
  - .claude/skills/hitl-evaluator/SKILL.md
  - .claude/skills/gmail-processor/SKILL.md
  - .claude/skills/whatsapp-processor/SKILL.md
  - .claude/skills/linkedin-poster/SKILL.md
  - .claude/skills/scheduled-briefing/SKILL.md
- [ ] Update `.gitignore` for new vault folders (10 min)
- [ ] Run existing 69 tests — confirm nothing broken (5 min)
  ```bash
  uv run pytest tests/ -v
  ```

**Total: ~2.5h**

### Day 2 (3-4h) — Plan.md + --once Flag
- [ ] Implement Plan.md reasoning loop — S4 (2-3h)
  - Create full `plan-creator/SKILL.md` with format spec
  - Add `should_create_plan()` to orchestrator
  - Add `create_plan()` to orchestrator
  - Modify `run_cycle()` to call plan creation before processing
  - Write `tests/test_plan_creator.py` (6-8 tests)
  - Verify: drop an invoice.pdf, check Plans/ folder
- [ ] Add `--once` flag to orchestrator — S7 prep (30 min)
  - Add argparse to `main()`
  - Single cycle mode: process queue once, then exit
  - Write test for --once flag
- [ ] Run all tests (5 min)
  ```bash
  uv run pytest tests/ -v
  ```
- [ ] Git commit: "feat: Plan.md reasoning loop + --once orchestrator flag (S4, S7 prep)"

**Total: ~3h**

### Week 1 Checkpoint
- [ ] 5 new vault folders exist with .gitkeep
- [ ] config.py has all Silver constants
- [ ] Plan.md generates for invoice/contract/proposal docs
- [ ] --once flag works
- [ ] 6 SKILL.md stubs exist
- [ ] All tests pass (69 original + ~10 new = ~79)
- [ ] **Requirements touched: S4 DONE, S7 partial, S8 partial**

---

## Week 2: HITL + Gmail Setup (7-9h)

**Focus:** Safety infrastructure (HITL) and Gmail API setup — the two prerequisites for everything in weeks 3-4.

### Day 3 (3-4h) — HITL Approval Workflow
- [ ] Update `Company_Handbook.md` with approval rules (20 min)
  - Invoice > $500, contract < 7 days, all outbound emails/posts
- [ ] Implement `hitl-evaluator/SKILL.md` with full evaluation logic (30 min)
- [ ] Add HITL functions to `src/orchestrator.py` (2h)
  - `evaluate_hitl(meta_path)` — check if approval needed
  - `route_to_approval(meta_path, companion)` — move to Pending_Approval
  - `process_approved_files()` — poll Approved/ folder
  - `process_rejected_files()` — poll Rejected/ folder
  - Modify `run_cycle()` to integrate HITL check
- [ ] Write `tests/test_hitl.py` (1h)
  - test_invoice_high_priority_needs_approval
  - test_note_low_priority_no_approval
  - test_explicit_approval_flag
  - test_gmail_high_priority_needs_approval
  - test_file_moved_to_pending_approval
  - test_status_updated_to_pending_approval
  - test_approved_file_moved_to_done
  - test_rejected_file_moved_to_done
  - test_existing_bronze_flow_unaffected
- [ ] Run all tests (5 min)
- [ ] Git commit: "feat: HITL approval workflow (S6)"

**Total: ~4h**

### Day 4 (3-4h) — Google Cloud + Gmail Dependencies
- [ ] Create Google Cloud project "Zoya AI Employee" (30 min)
  - https://console.cloud.google.com
  - Enable Gmail API
  - Configure OAuth consent screen (External, test user = your email)
  - Scopes: gmail.readonly, gmail.modify, gmail.send
- [ ] Create OAuth2 Desktop credentials (15 min)
  - Download `credentials.json` to project root
  - Verify: `ls credentials.json && grep credentials.json .gitignore`
- [ ] First-run OAuth flow (15 min)
  - Run auth script → browser opens → consent → token.json saved
  - Verify: `ls token.json`
- [ ] Install Gmail dependencies (10 min)
  ```bash
  uv add google-api-python-client google-auth-oauthlib google-auth-httplib2
  ```
- [ ] Install MCP SDK (10 min)
  ```bash
  uv add mcp
  ```
- [ ] Begin Gmail watcher skeleton (1h)
  - Create `src/gmail_watcher.py` with authenticate(), get_service()
  - Test OAuth flow manually
- [ ] Git commit: "chore: Google Cloud setup + Gmail dependencies"

**Total: ~3h**

### Week 2 Checkpoint
- [ ] HITL routes high-priority items to /Pending_Approval/
- [ ] Moving files in Obsidian (Approved/Rejected) triggers completion
- [ ] Google Cloud project created with Gmail API enabled
- [ ] credentials.json and token.json exist and are gitignored
- [ ] Gmail dependencies installed
- [ ] All tests pass (~79 + ~12 HITL = ~91)
- [ ] **Requirements touched: S6 DONE, S2 started, S5 deps ready**

---

## Week 3: Gmail + MCP Server (8-10h)

**Focus:** Complete Gmail watcher and Email MCP server — the two highest-value Silver features.

### Day 5 (3-4h) — Gmail Watcher Implementation
- [ ] Complete `src/gmail_watcher.py` (2-3h)
  - `fetch_unread_messages()` — poll for unread
  - `get_message_detail()` — fetch full message
  - `extract_headers()` — parse From/To/Subject/Date
  - `extract_body()` — handle plain/multipart/snippet fallback
  - `save_attachments()` — download to /Inbox/
  - `create_email_file()` — markdown with source: gmail frontmatter
  - `mark_as_read()` — remove UNREAD label
  - `poll_once()` — single polling cycle
  - `main()` — continuous polling loop
- [ ] Write `tests/test_gmail_watcher.py` (1-2h)
  - test_extract_headers, test_missing_headers
  - test_simple_body, test_multipart_body, test_fallback_snippet
  - test_email_file_created_in_inbox
  - test_frontmatter_includes_source_gmail
  - test_subject_sanitized_in_filename
  - test_skips_already_processed
  - test_new_message_creates_file
- [ ] Add gmail-processor SKILL.md content (20 min)
- [ ] Manual test: start Gmail watcher, send yourself an email, verify .md appears in /Inbox/
- [ ] Run all tests
- [ ] Git commit: "feat: Gmail watcher (S2a)"

**Total: ~4h**

### Day 6 (3-4h) — Email MCP Server
- [ ] Create `src/mcp/__init__.py` (1 min)
- [ ] Implement `src/mcp/email_server.py` (2-3h)
  - `send_email(to, subject, body)` → creates approval file in /Pending_Approval/
  - `search_emails(query, max_results)` → searches Gmail via API
  - `list_recent_emails(count)` → wrapper for search
  - Server setup using `mcp` Python SDK
- [ ] Create `.claude/mcp.json` config (15 min)
- [ ] Write `tests/test_mcp_email.py` (1h)
  - test_send_email_creates_approval_file
  - test_send_email_does_not_actually_send
  - test_search_returns_formatted_results
  - test_search_empty_results
- [ ] Verify MCP connection (15 min)
  ```bash
  claude mcp list  # Should show "email" server
  ```
- [ ] Run all tests
- [ ] Git commit: "feat: Email MCP server (S5)"

**Total: ~4h**

### Week 3 Checkpoint
- [ ] Gmail watcher polls and creates .md files in /Inbox/
- [ ] Emails flow through full pipeline: Gmail → Inbox → Needs_Action → Done
- [ ] MCP server listed in `claude mcp list`
- [ ] send_email creates approval file (never sends directly)
- [ ] search_emails returns formatted results
- [ ] All tests pass (~91 + ~20 = ~111)
- [ ] **Requirements touched: S2a DONE, S5 DONE**

---

## Week 4: LinkedIn + WhatsApp + Scheduling (7-9h)

**Focus:** Complete remaining requirements. LinkedIn posting, second watcher, cron jobs.

### Day 7 (3-4h) — LinkedIn Auto-Posting
- [ ] Check LinkedIn API access status
  - If approved: implement API posting
  - If pending: implement with DRY_RUN=true (still demonstrates flow)
- [ ] Implement `src/linkedin_poster.py` (2-3h)
  - `generate_post_content()` — Claude generates post from business context
  - `create_approval_request(content)` — writes to /Pending_Approval/
  - `post_to_linkedin(content)` — API post or dry-run
  - `process_approved_posts()` — check /Approved/ for LinkedIn posts
  - `main()` — generate + route for approval
- [ ] Fill in `linkedin-poster/SKILL.md` (20 min)
- [ ] Write `tests/test_linkedin_poster.py` (1h)
  - test_content_generation
  - test_approval_file_created
  - test_dry_run_mode
  - test_approved_post_processed
- [ ] Manual test: run linkedin_poster, check /Pending_Approval/
- [ ] Run all tests
- [ ] Git commit: "feat: LinkedIn auto-posting with HITL (S3)"

**Total: ~4h**

### Day 8 (2-3h) — WhatsApp Watcher + Cron
- [ ] WhatsApp Watcher — S2b (2h)
  - Install: `uv add flask twilio`
  - Implement `src/whatsapp_watcher.py` (Flask webhook)
  - Fill in `whatsapp-processor/SKILL.md`
  - Write `tests/test_whatsapp_watcher.py`
  - Setup: Twilio account + sandbox + ngrok
  - **If Twilio setup is blocked:** create the code anyway + document setup steps. Gmail + File System = 2 watchers (minimum met).
- [ ] Cron Jobs — S7 (30 min)
  ```bash
  crontab -e
  # Add: daily orchestrator --once at 8 AM
  # Add: weekly LinkedIn post at Monday 9 AM
  # Add: weekly briefing at Monday 8 AM
  ```
  - Verify: `crontab -l`
- [ ] Fill in `scheduled-briefing/SKILL.md` (15 min)
- [ ] Run all tests
- [ ] Git commit: "feat: WhatsApp watcher + cron scheduling (S2b, S7)"

**Total: ~3h**

### Week 4 Checkpoint
- [ ] LinkedIn poster generates content and creates approval files
- [ ] WhatsApp watcher receives messages (or code is ready + documented)
- [ ] Cron jobs installed and verified
- [ ] All tests pass (~111 + ~15 = ~126)
- [ ] **Requirements touched: S3 DONE, S2b DONE, S7 DONE**

---

## Week 5: Integration + Polish (3-4h)

**Focus:** End-to-end testing, start script, demo preparation.

### Day 9 (2-3h) — Integration + Polish
- [ ] Create `scripts/start_silver.sh` (20 min)
  - Launches watcher + gmail_watcher + orchestrator
  - Trap for clean shutdown
  - `chmod +x scripts/start_silver.sh`
- [ ] Update `pyproject.toml` with all entry points (10 min)
  - zoya-gmail, zoya-whatsapp, zoya-linkedin
- [ ] End-to-end integration testing (1-2h)
  - Scenario 1: File drop → pipeline → Done (Bronze regression)
  - Scenario 2: Gmail → pipeline → Done
  - Scenario 3: Invoice → Plan.md → HITL → Approval → Done
  - Scenario 4: LinkedIn → HITL → Approval → Post (dry-run)
  - Scenario 5: Orchestrator --once → single cycle → exit
- [ ] Verify all 9 Agent Skills have SKILL.md files
  ```bash
  ls .claude/skills/*/SKILL.md | wc -l  # Should be 9
  ```
- [ ] Update Dashboard.md template for Silver sections
- [ ] Run full test suite
  ```bash
  uv run pytest tests/ -v --tb=short
  ```
- [ ] Git commit: "feat: Silver tier integration + polish"

### Day 10 (1-2h) — Demo Prep
- [ ] Record demo video (5-10 min) covering:
  1. All processes starting (start_silver.sh)
  2. File drop → Done (Bronze flow)
  3. Gmail watcher picking up email
  4. Plan.md generated for invoice
  5. HITL approval flow in Obsidian
  6. LinkedIn poster approval file
  7. MCP server listed (`claude mcp list`)
  8. Cron jobs (`crontab -l`)
  9. All 9 skills (`ls .claude/skills/`)
- [ ] Final git tag: `silver-tier-complete`

**Total: ~4h**

---

## Weekly Hour Summary

| Week | Focus | Hours | Cumulative |
|------|-------|-------|------------|
| Week 1 | Foundation + Plan.md + --once | 6-8h | 6-8h |
| Week 2 | HITL + Google Cloud setup | 7-8h | 13-16h |
| Week 3 | Gmail Watcher + MCP Server | 8-10h | 21-26h |
| Week 4 | LinkedIn + WhatsApp + Cron | 7-9h | 28-35h |
| Week 5 | Integration + Demo | 3-4h | 31-39h |
| **TOTAL** | | **31-39h** | |

---

## Requirement Completion Timeline

| Req | Description | Completed By | Week |
|-----|-------------|--------------|------|
| S1 | Bronze requirements passing | Already done | — |
| S4 | Plan.md reasoning loop | Day 2 | Week 1 |
| S7 | Basic scheduling (--once + cron) | Day 2 + Day 8 | Week 1 + 4 |
| S8 | All AI as Agent Skills | Day 1 (stubs) + ongoing | Week 1-4 |
| S6 | HITL approval workflow | Day 3 | Week 2 |
| S2 | Two+ watchers (Gmail + WhatsApp) | Day 5 + Day 8 | Week 3 + 4 |
| S5 | MCP server (email) | Day 6 | Week 3 |
| S3 | LinkedIn auto-posting | Day 7 | Week 4 |

---

## Minimum Viable Silver (if time is short)

If you can only spend 18-20 hours, skip WhatsApp and do LinkedIn in dry-run:

| Item | Hours | Covers |
|------|-------|--------|
| Foundation + config | 2h | S8 partial |
| Plan.md loop | 2.5h | S4 |
| --once flag | 0.5h | S7 partial |
| HITL workflow | 4h | S6 |
| Google Cloud + Gmail | 5h | S2 (Gmail + File System = 2 watchers) |
| MCP email server | 4h | S5 |
| LinkedIn (dry-run) | 2h | S3 |
| Cron setup | 0.5h | S7 |
| **TOTAL** | **20.5h** | **All 8 requirements** |

This skips WhatsApp entirely (Gmail + File System = 2 watchers minimum) and uses dry-run LinkedIn posting.
