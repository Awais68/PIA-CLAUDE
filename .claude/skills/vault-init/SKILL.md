# Vault Init Skill

## Description

First-time setup skill. Creates the complete vault folder structure and initial template files for Zoya.

## Trigger

Manual — run once during initial setup.

## Instructions

1. **Create the folder structure** under `AI_Employee_Vault/`:

```
AI_Employee_Vault/
├── Dashboard.md
├── Company_Handbook.md
├── Inbox/
├── Needs_Action/
├── In_Progress/
├── Done/
├── Quarantine/
└── Logs/
```

2. **Create `Dashboard.md`** with the initial template (all counts at 0, status "Stopped").

3. **Create `Company_Handbook.md`** with the default rules of engagement.

4. **Verify** all folders exist and are writable.

5. **Report** the result — list each path and whether it was created or already existed.

## Usage

```bash
claude "Initialize the Zoya vault using the vault-init skill"
```

## Notes

- This skill is idempotent — running it again will not overwrite existing files.
- Only creates files/folders that are missing.
- Does not delete any existing content.
