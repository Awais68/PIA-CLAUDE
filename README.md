# Zoya - Personal AI Employee

> Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

Zoya is a Personal AI Employee built for the **FTE Hackathon 0**. She autonomously manages personal and freelance/consulting business affairs using Claude Code as the brain and Obsidian as the dashboard.

**Current Tier:** Bronze (Foundation)

---

## What Zoya Does

Drop a document into the `/Inbox/` folder and Zoya will:

1. **Detect** it automatically via the File System Watcher
2. **Read** the document (PDF, DOCX, or Markdown)
3. **Summarize** it in 2-3 sentences
4. **Extract action items** - deadlines, tasks, follow-ups
5. **Categorize** it - invoice, contract, proposal, receipt, note
6. **Update the Dashboard** in Obsidian with the latest activity
7. **Archive** the processed item in `/Done/`

All of this happens locally. No data leaves your machine.

---

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   You drop   │────>│  File System     │────>│  /Needs_     │
│   file in    │     │  Watcher (Python) │     │  Action/     │
│   /Inbox/    │     └──────────────────┘     └──────┬───────┘
└──────────────┘                                      │
                                                      v
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Obsidian    │<────│  Claude Code     │<────│  inbox-      │
│  Dashboard   │     │  (Reasoning)     │     │  processor   │
│              │     └──────────────────┘     │  skill       │
└──────────────┘                              └──────────────┘
```

See [AGENTS.md](./AGENTS.md) for full architecture details.

---

## Project Structure

```
PIA-CLAUDE/
├── AGENTS.md                  # Agent architecture & skill design
├── README.md                  # This file
├── requirements.md            # Hackathon requirements
├── .gitignore
│
├── AI_Employee_Vault/         # Obsidian vault (created during setup)
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Inbox/                 # Drop files here
│   ├── Needs_Action/          # Processing queue
│   ├── Done/                  # Completed items
│   └── Logs/                  # Audit logs
│
├── src/                       # Python source code
│   ├── watchers/
│   │   ├── base_watcher.py    # Abstract base class for all watchers
│   │   └── filesystem_watcher.py  # File System Watcher
│   └── orchestrator.py        # Master process coordinator
│
├── .claude/skills/            # Claude Code Agent Skills
│   ├── inbox-processor/
│   │   └── SKILL.md
│   ├── dashboard-updater/
│   │   └── SKILL.md
│   └── vault-init/
│       └── SKILL.md
│
├── pyproject.toml             # Python project config (uv)
└── .env                       # Secrets (never committed)
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| [Claude Code](https://claude.com/product/claude-code) | Latest | AI reasoning engine |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base & dashboard |
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [uv](https://docs.astral.sh/uv/) | Latest | Python package manager |
| [Git](https://git-scm.com/) | Latest | Version control |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd PIA-CLAUDE
uv sync
```

### 2. Initialize the Obsidian vault

```bash
# Claude Code will create the vault structure
# Use the vault-init skill
claude "Initialize the Zoya vault"
```

Or open Claude Code in this directory and ask:
> "Run the vault-init skill to set up the AI_Employee_Vault"

### 3. Open the vault in Obsidian

Open Obsidian -> "Open folder as vault" -> select `AI_Employee_Vault/`

### 4. Start the File System Watcher

```bash
uv run python src/watchers/filesystem_watcher.py
```

### 5. Drop files and watch Zoya work

Drop any PDF, DOCX, or Markdown file into `AI_Employee_Vault/Inbox/`.

---

## Agent Skills

All AI functionality is modular via Claude Code Agent Skills:

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `inbox-processor` | Summarize, extract actions, categorize documents | New file in `/Needs_Action/` |
| `dashboard-updater` | Refresh Dashboard.md with current status | After processing completes |
| `vault-init` | First-time vault setup | Manual |

---

## Bronze Tier Checklist

- [ ] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- [ ] File System Watcher script monitoring `/Inbox/`
- [ ] Claude Code reading from and writing to the vault
- [ ] Basic folder structure: `/Inbox/`, `/Needs_Action/`, `/Done/`
- [ ] All AI functionality as Agent Skills

---

## Roadmap

| Tier | Features | Status |
|------|----------|--------|
| **Bronze** | File Watcher + Vault + Dashboard + Skills | In Progress |
| Silver | Gmail Watcher + WhatsApp + MCP + HITL approval | Planned |
| Gold | CEO Briefing + Ralph Wiggum loop + Odoo + Social Media | Planned |
| Platinum | Cloud deployment + 24/7 operation | Planned |

---

## Tech Stack

- **Brain:** Claude Code (Opus)
- **Memory/GUI:** Obsidian (local Markdown)
- **Senses:** Python + watchdog (File System Watcher)
- **Package Manager:** uv
- **Skills:** Claude Code Agent Skills

---

## Security

- All data stays local - no external API calls in Bronze tier
- No credentials stored in the vault
- `.env` file in `.gitignore`
- Every AI action logged to `/Logs/`

---

## Hackathon

**Hackathon:** Personal AI Employee Hackathon 0 - Building Autonomous FTEs in 2026
**Tier Target:** Bronze (Foundation)
**Submission:** [Google Form](https://forms.gle/JR9T1SJq5rmQyGkGA)
