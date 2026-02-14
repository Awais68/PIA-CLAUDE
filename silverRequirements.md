# Silver Tier Official Requirements

**Source:** Personal AI Employee Hackathon 0 — Official Spec (lines 132-151)
**Tier:** Silver - Functional Assistant
**Estimated Time:** 20-30 hours
**Prerequisite:** All Bronze Tier requirements complete

---

## Mandatory Deliverables

- [ ] **S1: All Bronze requirements passing**
  - Obsidian vault with Dashboard.md and Company_Handbook.md
  - One working Watcher script (file system monitoring)
  - Claude Code reading from and writing to the vault
  - Basic folder structure: /Inbox, /Needs_Action, /Done
  - All AI functionality implemented as Agent Skills

- [ ] **S2: Two or more Watcher scripts**
  - Exact text: *"Two or more Watcher scripts (e.g., Gmail + Whatsapp + LinkedIn)"*
  - Minimum 2 watchers beyond file system (pick from: Gmail, WhatsApp, LinkedIn)
  - Each watcher must funnel into the existing pipeline

- [ ] **S3: Automatically Post on LinkedIn**
  - Exact text: *"Automatically Post on LinkedIn about business to generate sales"*
  - Automated content generation for business promotion
  - Posting to LinkedIn (via API, MCP, or browser automation)

- [ ] **S4: Claude reasoning loop that creates Plan.md files**
  - Exact text: *"Claude reasoning loop that creates Plan.md files"*
  - When Claude processes a complex task, it writes a Plan.md with:
    - Objective, steps (checkboxes), dependencies, approval gates
  - Demonstrates structured multi-step reasoning (not just one-shot processing)

- [ ] **S5: One working MCP server for external action**
  - Exact text: *"One working MCP server for external action (e.g., sending emails)"*
  - At least one MCP server that Claude can use as a tool
  - Must perform a real external action (send email, post content, etc.)

- [ ] **S6: Human-in-the-loop approval workflow**
  - Exact text: *"Human-in-the-loop approval workflow for sensitive actions"*
  - File-based approval system (Pending_Approval -> Approved/Rejected)
  - Orchestrator blocks on sensitive actions until human approves
  - Configurable thresholds (what requires approval vs auto-proceed)

- [ ] **S7: Basic scheduling via cron or Task Scheduler**
  - Exact text: *"Basic scheduling via cron or Task Scheduler"*
  - At least one scheduled task (daily briefing, periodic check, etc.)
  - Can use: cron (Linux/Mac), Task Scheduler (Windows), or Python schedule lib

- [ ] **S8: All AI functionality as Agent Skills**
  - Exact text: *"All AI functionality should be implemented as Agent Skills"*
  - Every new Silver feature needs a corresponding SKILL.md in `.claude/skills/`
  - Skills: gmail-processor, whatsapp-processor, linkedin-poster, plan-creator, hitl-approver, etc.

---

## Key Notes

### Prerequisites
- Bronze Tier complete (5/5 requirements, all tests passing)
- Python 3.13+ with uv
- Claude Code active subscription
- Obsidian vault operational with /Inbox, /Needs_Action, /Done
- Agent Skills architecture in place

### Success Criteria
- All 8 deliverables functional and demonstrable
- End-to-end flow: external input -> watcher -> orchestrator -> Claude -> action
- At least one flow requires human approval before execution
- At least one scheduled/automated task runs without manual trigger
- LinkedIn posting works (even if in dry-run/sandbox mode for demo)
- Plan.md files generated for multi-step tasks
- Demo video showing all Silver features (5-10 min)

### Judging Weights (from spec)
| Criterion | Weight |
|-----------|--------|
| Functionality | 30% |
| Innovation | 25% |
| Practicality | 20% |
| Security | 15% |
| Documentation | 10% |

### Warnings
- **WhatsApp**: Playwright-based approach is unofficial, may break. Consider Twilio sandbox as fallback.
- **LinkedIn API**: Restricted access. LinkedIn API requires app review for posting. Alternatives: browser automation (Playwright), or use a pre-approved integration.
- **OAuth tokens**: Gmail and LinkedIn both require OAuth2 setup. Tokens expire — handle refresh.
- **Rate limits**: Gmail API (250 quota units/sec), LinkedIn API (strict daily limits).
- **Never commit secrets**: credentials.json, token.json, .env must stay in .gitignore.
- **Agent Skills**: Every new piece of AI functionality MUST be a SKILL.md — this is a hard requirement, not optional.
