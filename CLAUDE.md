AGENTS.md

# Zoya - Personal AI Employee

- Read AGENTS.md for full architecture and component details.
- All AI functionality must be implemented as Agent Skills in `.claude/skills/`.
- The vault lives at `AI_Employee_Vault/` — never hardcode absolute paths.
- Python source code lives in `src/` — managed with `uv`.
- Never commit secrets (.env, credentials.json, token.json).
- When processing documents, write results to metadata files only — never modify original documents.
- File movement between folders is the orchestrator's job, not Claude's.
