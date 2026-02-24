# PLATINUM TIER - COMPLETE FOLDER STRUCTURE

## AI_Employee_Vault/ (Synced via Git)

```
AI_Employee_Vault/
├── Skills/                          # All skill definitions (md files)
│   ├── vault_sync_skill.md
│   ├── cloud_agent_skill.md
│   ├── local_agent_skill.md
│   ├── work_zone_skill.md
│   ├── platinum_security_skill.md
│   ├── health_monitor_skill.md
│   ├── platinum_demo_skill.md
│   ├── a2a_upgrade_skill.md
│   └── README.md                    # Skills index
│
├── Dashboard.md                     # LOCAL ONLY — final single source of truth
│
├── Needs_Action/                    # Tasks waiting to be claimed
│   ├── EMAIL_*.md                   # From cloud Gmail watcher
│   ├── LINKEDIN_*.md                # From cloud LinkedIn watcher
│   ├── TWITTER_*.md                 # From cloud Twitter watcher
│   ├── WHATSAPP_*.md                # From cloud WhatsApp watcher
│   ├── ALERT_*.md                   # Health alerts
│   └── .gitkeep
│
├── In_Progress/
│   ├── cloud/                       # Tasks cloud agent is working on
│   │   ├── .gitkeep
│   │   └── *.md
│   └── local/                       # Tasks local agent is working on
│       ├── .gitkeep
│       └── *.md
│
├── Plans/                           # Task plans created by cloud
│   ├── email/
│   │   └── *.md
│   ├── social/
│   │   └── *.md
│   ├── invoice/
│   │   └── *.md
│   ├── general/
│   │   └── *.md
│   ├── briefing_data_*.md           # CEO briefing data from cloud
│   └── .gitkeep
│
├── Pending_Approval/                # Cloud → Local handoff (human reviews here)
│   ├── email/
│   │   ├── .gitkeep
│   │   └── EMAIL_DRAFT_*.md
│   ├── social/
│   │   ├── .gitkeep
│   │   └── SOCIAL_DRAFT_*.md
│   ├── invoice/
│   │   ├── .gitkeep
│   │   └── INVOICE_DRAFT_*.md
│   ├── whatsapp/
│   │   ├── .gitkeep
│   │   └── WHATSAPP_DRAFT_*.md
│   ├── payment/
│   │   ├── .gitkeep
│   │   └── PAYMENT_*.md
│   └── general/
│       ├── .gitkeep
│       └── *.md
│
├── Approved/                        # Human moves files here → Local executes
│   ├── email/
│   │   ├── .gitkeep
│   │   └── *.md
│   ├── social/
│   │   ├── .gitkeep
│   │   └── *.md
│   ├── invoice/
│   │   ├── .gitkeep
│   │   └── *.md
│   ├── whatsapp/
│   │   ├── .gitkeep
│   │   └── *.md
│   ├── payment/
│   │   ├── .gitkeep
│   │   └── *.md
│   └── general/
│       ├── .gitkeep
│       └── *.md
│
├── Rejected/                        # Human rejects drafts here
│   ├── .gitkeep
│   └── *.md
│
├── Done/                            # Completed tasks (audit trail)
│   ├── cloud/                       # Tasks completed by cloud
│   │   ├── .gitkeep
│   │   └── *.md
│   ├── local/                       # Tasks completed by local
│   │   ├── .gitkeep
│   │   └── *.md
│   └── archive/                     # Older completed tasks (>90 days)
│       └── .gitkeep
│
├── Updates/                         # Cloud status updates (local merges into Dashboard)
│   ├── cloud_status.md              # Cloud agent status + metrics
│   ├── orchestrator_status.md       # Cloud orchestrator heartbeat
│   └── metrics_YYYY-MM-DD.md        # Daily metrics from cloud
│
├── Signals/                         # Coordination signals (heartbeats, sync status)
│   ├── sync_status.md               # Last sync time + status
│   ├── sync_failed.md               # Alert if sync failed (both agents write)
│   ├── health_report.md             # Cloud health check results
│   ├── cloud_heartbeat_YYYY-MM-DD.md # Cloud VM heartbeat (updated every 5min)
│   ├── local_heartbeat_YYYY-MM-DD.md # Local machine heartbeat (when awake)
│   └── .gitkeep
│
├── Logs/                            # Audit trail (JSON logs, synced via git)
│   ├── cloud_YYYY-MM-DD.json        # Cloud agent actions (daily file)
│   ├── local_YYYY-MM-DD.json        # Local agent actions (daily file)
│   ├── sync_YYYY-MM-DD.json         # Vault sync events
│   ├── errors_YYYY-MM-DD.json       # Error log (both agents)
│   └── .gitkeep
│
├── Queue/                           # Retry queue for failed local executions
│   ├── email/
│   │   └── .gitkeep
│   ├── whatsapp/
│   │   └── .gitkeep
│   └── payment/
│       └── .gitkeep
│
├── Templates/                       # Markdown templates for task files
│   ├── email_task_template.md
│   ├── social_task_template.md
│   ├── invoice_task_template.md
│   ├── whatsapp_task_template.md
│   ├── payment_task_template.md
│   ├── approval_request_template.md
│   └── README.md
│
├── Archive/                         # Old completed tasks (retention: 90 days)
│   ├── 2026-01/
│   ├── 2026-02/
│   └── .gitkeep
│
├── .gitignore                       # CRITICAL: blocks secrets
├── README.md                        # Vault overview
└── .gitkeep
```

## src/ (Local + Cloud, managed with `uv`)

```
src/
├── cloud/
│   ├── setup_cloud_vm.sh            # Initial Oracle VM setup script
│   ├── pm2_ecosystem.config.js      # PM2 process manager config
│   ├── odoo_cloud_setup.sh          # Odoo deployment to cloud
│   └── enforce_gitignore.sh         # Verify no secrets in git
│
├── cloud_agent/
│   ├── __init__.py
│   ├── orchestrator.py              # Main cloud loop (claim → draft → approve)
│   ├── vault_sync.py                # Git sync (runs every 5 min)
│   ├── health_monitor.py            # System health checks
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── email_processor.py       # Draft email replies
│   │   ├── social_processor.py      # Draft social posts
│   │   ├── invoice_processor.py     # Draft Odoo invoices
│   │   └── general_processor.py     # General Claude reasoning
│   └── utils/
│       ├── __init__.py
│       ├── file_ops.py              # Claim-by-move + safe file ops
│       ├── logging.py               # Structured logging
│       └── config.py
│
├── local_agent/
│   ├── __init__.py
│   ├── on_wake.py                   # Runs when machine wakes (or via watchdog)
│   ├── executor.py                  # Execute approved actions via MCPs
│   ├── dashboard_manager.py         # Dashboard.md single writer
│   ├── mcp_clients/
│   │   ├── __init__.py
│   │   ├── email_client.py          # Send approved emails
│   │   ├── social_client.py         # Post approved social content
│   │   ├── whatsapp_client.py       # Send WhatsApp messages (local session)
│   │   ├── browser_client.py        # Execute payments (via browser MCP)
│   │   └── odoo_client.py           # Post approved invoices
│   └── utils/
│       ├── __init__.py
│       ├── keychain.py              # Read banking tokens from OS keychain
│       └── logging.py
│
├── watchers/
│   ├── __init__.py
│   ├── gmail_watcher.py             # Cloud: Watch Gmail → /Needs_Action/
│   ├── linkedin_watcher.py          # Cloud: Watch LinkedIn → /Needs_Action/
│   ├── twitter_watcher.py           # Cloud: Watch Twitter/X → /Needs_Action/
│   ├── whatsapp_watcher.py          # Cloud: Watch WhatsApp → /Needs_Action/
│   └── utils/
│       ├── __init__.py
│       └── normalizers.py           # Normalize task format
│
├── mcp_servers/
│   ├── __init__.py
│   ├── email_server.py              # MCP: send_email, read_email
│   ├── social_server.py             # MCP: post_linkedin, post_twitter, etc
│   ├── whatsapp_server.py           # MCP: send_whatsapp (local only)
│   ├── browser_server.py            # MCP: execute_payment, navigate
│   ├── odoo_server.py               # MCP: create_invoice, post_invoice, get_data
│   └── calendar_server.py           # MCP: read_calendar, schedule_event
│
├── test/
│   ├── __init__.py
│   ├── simulate_email.py            # Test: inject fake email into vault
│   ├── simulate_social.py           # Test: inject fake social task
│   ├── test_vault_sync.py           # Test: git sync logic
│   ├── test_claim_by_move.py        # Test: conflict prevention
│   ├── integration_tests.py         # End-to-end flow tests
│   └── README.md
│
├── config.py                        # Shared config (AGENT_ROLE, paths, etc)
├── requirements.txt                 # Python dependencies
└── README.md
```

## Project Root Files

```
project_root/
├── CLAUDE.md                        # This implementation plan
├── PLATINUM_FOLDER_STRUCTURE.md     # This file
├── .env.example                     # Secrets template (NEVER commit .env)
├── .gitignore                       # CRITICAL: blocks .env, secrets/
├── pyproject.toml                   # uv project config
├── uv.lock                          # Dependency lock file
├── README.md                        # Project overview
│
├── AI_Employee_Vault/               # Git-synced coordination vault
│   └── [folder structure above]
│
├── src/                             # Python code
│   └── [structure above]
│
├── logs/                            # Local log files (NOT synced)
│   ├── cloud_orchestrator.log
│   ├── vault_sync_local.log
│   ├── vault_sync_cloud.log
│   ├── local_agent_on_wake.log
│   └── health_monitor.log
│
├── tmp/                             # Temporary files (NOT synced)
│   ├── .gitkeep
│   └── [scratch space]
│
└── docs/
    ├── ARCHITECTURE.md              # System design overview
    ├── API_DOCS.md                  # MCP servers documentation
    ├── DEPLOYMENT.md                # Cloud VM setup guide
    ├── TROUBLESHOOTING.md           # Common issues + fixes
    └── SECURITY.md                  # Security guidelines
```

## .gitignore (ENFORCE AT ALL TIMES)

```
# SECRETS - NEVER COMMIT THESE
.env
*.env
.env.local
.env.*.local
whatsapp_session/
whatsapp_session.json
banking_tokens/
secrets/
.secrets/
*.token
*.key
*.pem
credentials.json
token.json
oauth_session.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.pytest_cache/

# Virtual environments
venv/
env/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Node
node_modules/
npm-debug.log

# PM2
logs/
.pm2/

# Claude Code
.claude/
.claude/memory/

# Local logs (NOT synced to git)
local_logs/
*.log

# Temporary
tmp/
.tmp/
.quarantine/
.backup_*

# OS
.DS_Store
Thumbs.db
```

## CRITICAL FILE: Vault/.gitignore

```
# THIS FILE PREVENTS SECRETS FROM SYNCING TO GIT
# Even though vault is synced, these NEVER go to git

# Local-only secrets (never cloud)
.env.local
whatsapp_session/
banking_tokens/
*.keychain
secrets/

# Application artifacts (not needed in sync)
.pytest_cache/
__pycache__/
*.pyc
```

## Key Files That MUST EXIST

### 1. AI_Employee_Vault/Dashboard.md
- LOCAL ONLY — local agent is sole writer
- Updated on every wake + after every local action
- Contains: summary, recent activity, pending approvals, metrics

### 2. AI_Employee_Vault/.gitignore
- Blocks all secrets from syncing
- Vault is synced, but secrets remain local

### 3. .env (on each machine, NEVER committed)
- Cloud VM: /home/ubuntu/ai_employee/.env
- Local: ~/.env or project_root/.env
- Contains all API keys, tokens, credentials

### 4. pyproject.toml
- Specifies Python 3.13+
- Lists all dependencies (anthropic, requests, pyyaml, etc)
- Managed with `uv`

## Directory Permissions & Ownership

| Directory | Owner | Permissions | Sync to Git |
|-----------|-------|-------------|------------|
| /Needs_Action/ | cloud (writes), local (reads) | 755 | ✅ YES |
| /In_Progress/cloud/ | cloud only | 755 | ✅ YES |
| /In_Progress/local/ | local only | 755 | ✅ YES |
| /Pending_Approval/ | cloud (writes), local (reads) | 755 | ✅ YES |
| /Approved/ | local only | 755 | ✅ YES |
| /Done/ | both | 755 | ✅ YES |
| /Logs/ | both append | 755 | ✅ YES (no secrets) |
| Dashboard.md | local only | 644 | ✅ YES |
| .env | machine-specific | 600 | ❌ NO (in .gitignore) |
| whatsapp_session/ | local only | 700 | ❌ NO (in .gitignore) |

## Initialization Checklist

- [ ] Create AI_Employee_Vault/ structure with all folders
- [ ] Create src/ structure with all Python modules
- [ ] Create .gitignore at project root (blocks .env, secrets/)
- [ ] Create .gitignore inside AI_Employee_Vault/ (extra protection)
- [ ] Create all skill .md files in AI_Employee_Vault/Skills/
- [ ] Create pyproject.toml with Python 3.13+ requirement
- [ ] Create initial Dashboard.md template
- [ ] Create .env.example (secrets template)
- [ ] Initialize git repository + private remote
- [ ] Create .gitkeep in all empty folders
- [ ] Test vault sync (pull, no errors)
- [ ] Test claim-by-move (move file, verify atomic)
- [ ] Run initial health check

## Next Steps

1. **Initialize Folders**: Use `mkdir -p` for all folders above
2. **Create Skill Files**: Add all .md files to AI_Employee_Vault/Skills/
3. **Create Python Modules**: Implement all src/ Python files
4. **Setup Git Repository**: Create private repo + add remote
5. **Test Vault Sync**: Verify pull/push works without secrets
6. **Deploy Cloud VM**: Run setup scripts on Oracle Cloud
7. **Run Demo**: Test Platinum flow (email → draft → approve → send)
