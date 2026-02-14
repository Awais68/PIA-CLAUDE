# Implementation Priority Matrix - Silver Tier

**Generated:** 2026-02-15
**Based on:** Silver_Tier_Blueprint.md + silverRequirements.md analysis

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| **HIGH** | Must do first — other tasks depend on this |
| **MEDIUM** | Can do in parallel once HIGH items are done |
| **LOW** | Polish/optional — complete if time allows |

---

## HIGH PRIORITY (Must Do First)

These items have downstream dependencies. Completing them unlocks everything else.

### 1. Vault Folder Setup + Config Updates
| Attribute | Value |
|-----------|-------|
| **Requirement** | Foundation for S4, S6, S7 |
| **Estimated Hours** | 0.5h |
| **Complexity** | Low |
| **Risk Level** | Low |
| **Dependencies** | None — zero external deps |
| **Impact** | Critical — every Silver feature needs these folders |
| **Details** | Create Plans/, Pending_Approval/, Approved/, Rejected/, Briefings/ folders. Add path constants to config.py. Update vault-init skill. |

### 2. Plan.md Reasoning Loop (S4)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S4 — Claude reasoning loop that creates Plan.md files |
| **Estimated Hours** | 2-3h |
| **Complexity** | Low |
| **Risk Level** | Low |
| **Dependencies** | Vault folders (item #1) |
| **Impact** | HIGH — demonstrates structured reasoning. Every subsequent task benefits from having Plan.md generated. Quick demo win. |
| **Details** | New skill: plan-creator/SKILL.md. Orchestrator changes: should_create_plan() + create_plan(). Tests: test_plan_creator.py. |

### 3. HITL Approval Workflow (S6)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S6 — Human-in-the-loop approval for sensitive actions |
| **Estimated Hours** | 4-5h |
| **Complexity** | Medium |
| **Risk Level** | Medium — modifies orchestrator core loop |
| **Dependencies** | Vault folders (item #1), Plan.md (item #2 — plan identifies what needs approval) |
| **Impact** | CRITICAL — MCP server, LinkedIn poster, and email sending all require HITL. Must be in place before any external action capability. |
| **Details** | New skill: hitl-evaluator/SKILL.md. Orchestrator: evaluate_hitl(), route_to_approval(), process_approved_files(), process_rejected_files(). Tests: test_hitl.py. Update Company_Handbook.md with approval rules. |

### 4. `--once` Flag for Orchestrator (S7 Prep)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S7 — enables cron scheduling |
| **Estimated Hours** | 0.5h |
| **Complexity** | Low |
| **Risk Level** | Low |
| **Dependencies** | None |
| **Impact** | HIGH — unlocks all scheduling. Trivial to implement but essential for cron jobs. |
| **Details** | Add argparse to orchestrator main(). --once runs single cycle and exits. |

### 5. Google Cloud + Gmail API Setup
| Attribute | Value |
|-----------|-------|
| **Requirement** | S2 (Gmail Watcher) + S5 (MCP Server) |
| **Estimated Hours** | 1h |
| **Complexity** | Low (but fiddly) |
| **Risk Level** | Medium — OAuth consent screen can be rejected |
| **Dependencies** | None (can do in parallel with items #1-4) |
| **Impact** | CRITICAL — Gmail watcher AND MCP email server both need these credentials. One setup, two features unlocked. |
| **Details** | Create Google Cloud project, enable Gmail API, create OAuth2 Desktop credentials, download credentials.json, first-run auth flow. |

---

## MEDIUM PRIORITY (Can Do in Parallel)

Once HIGH items are done, these can be worked on independently.

### 6. Gmail Watcher (S2a)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S2 — Two or more Watcher scripts |
| **Estimated Hours** | 3-4h (after Google Cloud setup) |
| **Complexity** | Medium |
| **Risk Level** | Medium — Gmail API quirks, token refresh edge cases |
| **Dependencies** | Google Cloud setup (item #5), Gmail dependencies installed |
| **Impact** | HIGH — first external watcher. Combined with file system watcher = 2 watchers minimum. |
| **Details** | src/gmail_watcher.py: authenticate(), poll_once(), create_email_file(), mark_as_read(). Skill: gmail-processor/SKILL.md. Tests: test_gmail_watcher.py. |

### 7. Email MCP Server (S5)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S5 — One working MCP server for external action |
| **Estimated Hours** | 3-4h |
| **Complexity** | Medium |
| **Risk Level** | Medium — MCP SDK is newer, expect debugging |
| **Dependencies** | Google Cloud setup (item #5), HITL workflow (item #3) — send_email routes through approval |
| **Impact** | HIGH — demonstrates Claude using tools for external actions. Core Silver feature. |
| **Details** | src/mcp/email_server.py: send_email, search_emails, list_recent_emails tools. .claude/mcp.json config. Tests: test_mcp_email.py. |

### 8. LinkedIn Auto-Posting (S3)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S3 — Automatically post on LinkedIn about business |
| **Estimated Hours** | 3-4h |
| **Complexity** | Medium |
| **Risk Level** | HIGH — LinkedIn API access requires app review (may take days) |
| **Dependencies** | HITL workflow (item #3) — all posts must go through approval |
| **Impact** | MEDIUM-HIGH — required Silver feature. Dry-run mode is acceptable fallback. |
| **Details** | src/linkedin_poster.py: generate_post_content(), create_approval_request(), post_to_linkedin(). Skill: linkedin-poster/SKILL.md. Start with DRY_RUN=true. |

### 9. Cron Job Setup (S7)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S7 — Basic scheduling via cron |
| **Estimated Hours** | 0.5h |
| **Complexity** | Low |
| **Risk Level** | Low |
| **Dependencies** | --once flag (item #4), orchestrator working |
| **Impact** | MEDIUM — demonstrates automation. Easy points. |
| **Details** | crontab entries: daily dashboard refresh (8 AM), weekly LinkedIn post (Mon 9 AM), weekly briefing (Mon 8 AM). |

---

## LOW PRIORITY (Polish/Optional)

Complete these after all HIGH and MEDIUM items work. Nice-to-have for demo.

### 10. WhatsApp Watcher (S2b)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S2 — Second additional watcher (beyond Gmail) |
| **Estimated Hours** | 3-4h |
| **Complexity** | Medium |
| **Risk Level** | HIGH — Twilio requires ngrok for webhook, fragile for demo |
| **Dependencies** | HITL workflow (item #3) |
| **Impact** | LOW-MEDIUM — Gmail + File System already satisfies "Two+ watchers". WhatsApp is a bonus third watcher. |
| **Details** | src/whatsapp_watcher.py (Flask webhook), Twilio sandbox setup, ngrok tunnel. Skill: whatsapp-processor/SKILL.md. Tests: test_whatsapp_watcher.py. |

### 11. SKILL.md Stubs for All Features (S8)
| Attribute | Value |
|-----------|-------|
| **Requirement** | S8 — All AI functionality as Agent Skills |
| **Estimated Hours** | 1h |
| **Complexity** | Low |
| **Risk Level** | Low |
| **Dependencies** | Should be done alongside each feature |
| **Impact** | MEDIUM — required for compliance. Create stubs early, fill in details as features are built. |
| **Details** | 6 new SKILL.md files: plan-creator, hitl-evaluator, gmail-processor, whatsapp-processor, linkedin-poster, scheduled-briefing. |

### 12. Start Script + Process Management
| Attribute | Value |
|-----------|-------|
| **Requirement** | None — convenience feature |
| **Estimated Hours** | 0.5h |
| **Complexity** | Low |
| **Risk Level** | Low |
| **Dependencies** | All watchers implemented |
| **Impact** | LOW — nice for demo but not a requirement. |
| **Details** | scripts/start_silver.sh: launches watcher, gmail_watcher, orchestrator with trap for cleanup. |

### 13. Weekly Briefing Generation
| Attribute | Value |
|-----------|-------|
| **Requirement** | Part of S7 — scheduled task output |
| **Estimated Hours** | 1h |
| **Complexity** | Low |
| **Risk Level** | Low |
| **Dependencies** | Cron setup (item #9), scheduled-briefing skill |
| **Impact** | LOW — supplementary to cron requirement. Good demo material. |
| **Details** | scheduled-briefing/SKILL.md. Cron entry generates briefing to Briefings/ folder. |

---

## Dependency Graph

```
                    ┌──────────────────┐
                    │ #1 Vault Folders │
                    │   + Config.py    │
                    └────────┬─────────┘
                             │
               ┌─────────────┼──────────────┐
               │             │              │
               ▼             ▼              ▼
        ┌──────────┐  ┌───────────┐  ┌──────────┐
        │ #2 Plan  │  │ #3 HITL   │  │ #4 --once│
        │ .md Loop │  │ Workflow  │  │   Flag   │
        └──────────┘  └─────┬─────┘  └────┬─────┘
                            │              │
         ┌──────────────────┼──────────┐   │
         │                  │          │   │
         ▼                  ▼          ▼   ▼
  ┌──────────────┐  ┌──────────┐  ┌──────────┐
  │ #8 LinkedIn  │  │ #7 Email │  │ #9 Cron  │
  │   Poster     │  │   MCP    │  │   Jobs   │
  └──────────────┘  └──────────┘  └──────────┘
                         │
   ┌─────────────────────┘
   │
   ▼
┌──────────────────┐      ┌───────────────┐
│ #5 Google Cloud  │─────>│ #6 Gmail      │
│    Setup         │      │    Watcher    │
└──────────────────┘      └───────────────┘

Independent (any time after #3):
┌──────────────────┐
│ #10 WhatsApp     │
│     Watcher      │
└──────────────────┘
```

---

## Summary

| Priority | Items | Total Hours | % of Work |
|----------|-------|-------------|-----------|
| HIGH | 5 items (#1-#5) | 8-10h | 30% |
| MEDIUM | 4 items (#6-#9) | 10-13h | 40% |
| LOW | 4 items (#10-#13) | 5-7h | 20% |
| Buffer (testing, debugging) | — | 3-4h | 10% |
| **TOTAL** | **13 items** | **26-34h** | **100%** |

### Critical Path (minimum to pass Silver)
1. Vault Folders → 2. Plan.md → 3. HITL → 4. --once Flag → 5. Google Cloud → 6. Gmail Watcher → 7. MCP Server → 8. LinkedIn (dry-run) → 9. Cron
**Minimum viable Silver: ~20-24h**
