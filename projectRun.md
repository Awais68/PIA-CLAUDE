# Zoya - Project Run Guide

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Ollama (if using `AI_PROVIDER=ollama`) — free, local, no API key
- Claude Code CLI (only if using `AI_PROVIDER=claude`)
- Obsidian (optional, for visual dashboard)

---

## 1. Install Dependencies

```bash
cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"
uv sync
```

---

## 2. Configure AI Provider

Edit `.env` to switch providers. Three options available:

### Option A: Ollama — Local Qwen (default, recommended for demo)

**One-time setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the Qwen model (~2.5 GB download)
ollama pull qwen3:4b
```

**In `.env`:**
```env
AI_PROVIDER=ollama
OLLAMA_MODEL=qwen3:4b
OLLAMA_BASE_URL=http://localhost:11434/v1
```

Available Ollama models:
| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `qwen3:4b` | ~2.5 GB | Fast | Good for demo |
| `qwen3:8b` | ~5 GB | Medium | Better quality |
| `qwen3:14b` | ~9 GB | Slower | Best quality |
| `qwen3:1.7b` | ~1 GB | Fastest | Lighter tasks |

### Option B: Qwen via DashScope API

```env
AI_PROVIDER=qwen
DASHSCOPE_API_KEY=sk-your-dashscope-key
QWEN_MODEL=qwen-plus
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### Option C: Claude Code CLI

```env
AI_PROVIDER=claude
```

Requires: `npm install -g @anthropic/claude-code`

---

## 3. Start the System

You need **2 terminals** running side by side.

**Make sure Ollama is running first** (if using Ollama provider):
```bash
ollama serve
```
> Note: If Ollama was installed via the system installer, it may already be running as a service.

### Terminal 1 — File Watcher

Monitors `AI_Employee_Vault/Inbox/` for new documents:

```bash
cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"
uv run zoya-watcher
```

You should see:
```
[watcher] INFO: Watcher started — monitoring .../AI_Employee_Vault/Inbox
```

### Terminal 2 — Orchestrator

Processes queued documents using AI:

```bash
cd "/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE"
uv run zoya-orchestrator
```

You should see:
```
[orchestrator] INFO: Orchestrator started (PID xxxxx)
```

---

## 4. Test It — Drop a File

### Terminal 3 — Drop a test document

```bash
cp test_samples/sample_invoice.md AI_Employee_Vault/Inbox/
```

Or create your own test file:

```bash
echo "# Meeting Notes
Date: Feb 17, 2026
Attendees: Ali, Sara, Ahmed

## Decisions
- Launch new website by March 1st
- Hire 2 developers by end of February

## Action Items
- [ ] Ali: Send proposal to client by Feb 20
- [ ] Sara: Set up staging server
- [ ] Ahmed: Review budget and approve
" > AI_Employee_Vault/Inbox/meeting_notes.md
```

### What to watch

1. **Terminal 1 (Watcher):** `Queued for processing: meeting_notes.md -> FILE_...md`
2. **Terminal 2 (Orchestrator):** `Invoking Ollama (qwen3:4b) for: meeting_notes.md`
3. **Terminal 2 (Orchestrator):** `Ollama processed successfully` → `Moved to Done`
4. Check the result: `cat AI_Employee_Vault/Done/FILE_*_meeting_notes.md`

---

## 5. View Dashboard in Obsidian

1. Open Obsidian
2. **File → Open folder as vault** → select `AI_Employee_Vault/`
3. Open `Dashboard.md` — shows live queue counts and recent activity

---

## 6. Supported File Types

| Type | Extension | Notes |
|------|-----------|-------|
| Markdown | `.md` | Fully supported (all providers) |
| PDF | `.pdf` | Text extracted and processed |
| Word | `.docx` | Text extracted and processed |

Max file size: **10 MB**

---

## 7. Folder Structure (Vault Lifecycle)

```
AI_Employee_Vault/
├── Inbox/          ← DROP FILES HERE
├── Needs_Action/   ← Watcher queues files here
├── In_Progress/    ← Orchestrator claims files here
├── Done/           ← Successfully processed (with AI summary)
├── Quarantine/     ← Failed after 3 retries
├── Logs/           ← Audit trail
└── Dashboard.md    ← Live status
```

---

## 8. Troubleshooting

### "Another orchestrator is already running"

```bash
rm orchestrator.lock.pid
```

### Watcher not detecting files

The watcher uses `on_created` events. If the file already exists in Inbox, remove it first then copy again:

```bash
rm AI_Employee_Vault/Inbox/myfile.md
cp /path/to/myfile.md AI_Employee_Vault/Inbox/
```

### Ollama errors

- Make sure Ollama is running: `ollama serve` (or check `systemctl status ollama`)
- Make sure model is pulled: `ollama pull qwen3:4b`
- Test it manually: `ollama run qwen3:4b "Hello"`
- Check if port 11434 is in use: `curl http://localhost:11434/api/tags`

### Qwen/DashScope API errors

- Verify your DashScope API key in `.env`
- Check balance at https://dashscope.console.aliyun.com/
- Try a cheaper model: `QWEN_MODEL=qwen-turbo`

### Claude "nested session" error

If running orchestrator from within Claude Code, the `CLAUDECODE` env var is automatically stripped (already patched).

---

## 9. Run Tests

```bash
uv run pytest tests/ -v
```

---

## 10. Stop the System

Press `Ctrl+C` in both Terminal 1 and Terminal 2.

---

## Silver Tier Features

### Gmail Watcher (S2)

**Setup:**
1. Create Google Cloud project + enable Gmail API
2. Download OAuth2 credentials to `credentials.json` in project root
3. Run: `uv run python scripts/setup_gmail_auth.py`

**Start:**
```bash
uv run zoya-gmail
```

### HITL Approval (S6)

Files needing approval appear in `AI_Employee_Vault/Pending_Approval/`.
- Move to `Approved/` to complete processing
- Move to `Rejected/` to discard

### Plan.md Reasoning (S4)

Invoices, contracts, and proposals automatically generate a Plan.md in `AI_Employee_Vault/Plans/` before processing.

### LinkedIn Auto-Posting (S3)

```bash
uv run zoya-linkedin
```
Creates drafts in `Pending_Approval/`. DRY_RUN mode by default.

### Email MCP Server (S5)

Configured in `.claude/mcp.json`. Tools: `send_email`, `search_emails`, `list_recent_emails`.

### Orchestrator --once (S7)

```bash
uv run zoya-orchestrator --once
```
Process one cycle and exit. Used for cron jobs.

### Start All Silver Services

```bash
./scripts/start_silver.sh
```

### Cron Setup (S7)

```bash
crontab scripts/crontab.example
```

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `uv sync` | Install/update dependencies |
| `ollama serve` | Start Ollama server (if not running) |
| `ollama pull qwen3:4b` | Download Qwen model |
| `uv run zoya-watcher` | Start file watcher |
| `uv run zoya-orchestrator` | Start orchestrator |
| `uv run zoya-orchestrator --once` | Single cycle (for cron) |
| `uv run zoya-gmail` | Start Gmail watcher |
| `uv run zoya-linkedin` | Process LinkedIn posts |
| `./scripts/start_silver.sh` | Start all Silver services |
| `uv run pytest tests/ -v` | Run test suite (136 tests) |
| `cat AI_Employee_Vault/Done/FILE_*.md` | View processed results |
| `cat AI_Employee_Vault/Dashboard.md` | View dashboard |
| `rm orchestrator.lock.pid` | Fix stale lock |
