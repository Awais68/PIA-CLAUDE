---
skill_name: VaultSync
version: 1.0
tier: Platinum
agent: both (cloud + local run independently)
trigger: "Every 5 minutes via PM2 cron (cloud) + watchdog (local)"
---

# VaultSync Skill - Git Coordination Backbone

## Objective
Keep Cloud and Local vaults in perfect sync via Git so both agents share the same state without direct network connection.

## Key Files
- Cloud implementation: `src/cloud_agent/vault_sync.py`
- Local implementation: `src/local_agent/vault_sync.py`
- Status tracking: `/Vault/Signals/sync_status.md`

## Sync Process
1. git pull --rebase origin main (with Dashboard.md protection)
2. Resolve conflicts (local wins for Dashboard.md)
3. git add -A (markdown + state files only)
4. git commit -m "sync: [agent_name] [timestamp]"
5. git push origin main

## Critical Rules
- .gitignore blocks: .env, *.token, whatsapp_session/, banking_tokens/, secrets/
- Single writer rule: Local owns Dashboard.md
- Claim-by-move: Atomic moves prevent double-processing
- Error handling: Retry 3x, then alert

## Testing
- Verify no secrets in git: `git check-ignore -v .env`
- Verify syncs work without network issues
- Verify Dashboard.md always kept from local
- Verify conflict resolution works

See full documentation in: `01_vault_sync_skill.md`
