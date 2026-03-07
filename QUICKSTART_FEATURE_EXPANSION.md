# Zoya Platinum Tier Expansion - Quick Start

## ✅ Implementation Complete
All 4 features implemented and syntax-validated.

---

## 🚀 Next Steps (15 minutes)

### Step 1: Install Dependencies
```bash
cd /media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150\ GB\ DATA\ TRANSFER/hackathon\ series/0\ FTE\ Hackathon/PIA-CLAUDE

uv add scikit-learn numpy discord.py google-generativeai anthropic
```

### Step 2: Update .env
Add these environment variables:
```bash
# Discord Bot (create at discord.com/developers)
DISCORD_TOKEN=<your_bot_token>
DISCORD_GUILD_ID=<your_server_id>
DISCORD_CHANNEL_ID=<your_channel_id>

# Gemini API (get from google ai studio)
GEMINI_API_KEY=<your_gemini_key>

# Anthropic (already have this)
ANTHROPIC_API_KEY=<your_key>
```

### Step 3: Test Each Component

#### Test Todo Manager
```bash
python -m src.todo_manager create "Test Task" "High" "2026-03-15"
python -m src.todo_manager list
python -m src.todo_manager complete T001
```

#### Test Email Drafter
```bash
python -m src.automations.email_drafter test
```

#### Test Research Agent
```bash
python -m src.research_agent --topics "BTC" --dry-run
```

#### Start Discord Bot
```bash
python -m src.watchers.discord_watcher
```

### Step 4: Test Discord Bot
In your Discord server:
- Type `/zoya`
- Click buttons: Tasks, Dashboard, Email, Expense, Todo, Research
- Try each modal (Expense, Todo, Email, Research)
- Verify files appear in `AI_Employee_Vault/Inbox/`

---

## 📁 What Was Created

### Core Modules (1,400 lines)
| File | Lines | Purpose |
|------|-------|---------|
| `src/todo_manager.py` | 300 | Full CRUD + Dashboard sync |
| `src/automations/email_drafter.py` | 200 | TF-IDF smart email drafting |
| `src/research_agent.py` | 350 | Research with Playwright + Gemini |
| `src/watchers/discord_watcher.py` | 500 | Discord bot with modals |
| `src/mcp_servers/discord_mcp.py` | 150 | MCP server integration |

### Configuration
| File | Changes |
|------|---------|
| `pyproject.toml` | +8 lines (5 deps + 4 entry points) |
| `src/config.py` | +15 lines (Discord/Gemini/Todo vars) |

### Data Storage
| File | Purpose |
|------|---------|
| `AI_Employee_Vault/todo.md` | Canonical todo storage |
| `AI_Employee_Vault/Research/` | Research reports (created on first use) |

### Skills
| File | Purpose |
|------|---------|
| `.claude/skills/draft-email/SKILL.md` | Email drafting instructions |
| `.claude/skills/todo-manager/SKILL.md` | Todo CRUD instructions |
| `.claude/skills/research-agent/SKILL.md` | Research orchestration |
| `.claude/skills/dashboard-updater/SKILL.md` | Updated with todo section |

---

## 📊 Feature Overview

### 1️⃣ Email Draft Skill
```
Incoming Email → TF-IDF Match (Done/) → Top 3 Similar Emails
  → Claude Draft with Context → Pending_Approval/
  → Human Review & Send
```

### 2️⃣ Discord Bot
```
/zoya → Menu (6 options)
/todo, /expense, /email, /research → Modals
Files Created → Inbox/ → Orchestrator → Needs_Action/ → Skills
```

### 3️⃣ Todo System
```
Discord /todo Modal → todo_manager.create_todo()
  → Update todo.md + Dashboard.md
  → Create Inbox task for approval
  → Human approves → Approved/
```

### 4️⃣ Research Agent
```
Discord /research → Playwright scrape (Google/Yahoo/CoinGecko)
  → Claude analysis (summary + sentiment)
  → Gemini generate infographic
  → Save Research/<topic>.md + images/
```

---

## 🔌 Discord Commands

```
/zoya              Main menu
/task              List tasks from Needs_Action/
/dashboard         View Dashboard.md
/expense           Modal: Amount, Category, Description, Date
/todo              Modal: Task, Priority, Due, Recurrence
/email             Modal: Subject, Context
/research          Modal: Topics (comma-separated), Schedule (optional)
```

---

## 🎯 Success Criteria

✅ **After Setup**, you should be able to:
- [ ] Create todos via Discord `/todo` command
- [ ] View todos in `todo.md` and `Dashboard.md`
- [ ] Add expenses via Discord (saved to `Inbox/EXPENSE_*.md`)
- [ ] Request email drafts (TF-IDF similarity matching)
- [ ] Request research on any topic (BTC, AAPL, etc.)
- [ ] See Discord bot stay alive on crashes (auto-restart)
- [ ] Approve/reject items through vault workflow

---

## 📝 Documentation Files

- **PLATINUM_TIER_EXPANSION_COMPLETE.md** - Comprehensive feature guide
- **QUICKSTART_FEATURE_EXPANSION.md** - This file (quick start)
- **.claude/skills/*/SKILL.md** - Skill instructions (for orchestrator)

---

## 🆘 Troubleshooting

### Discord Bot doesn't start
```
✓ Check DISCORD_TOKEN in .env (no typos)
✓ Check DISCORD_GUILD_ID and DISCORD_CHANNEL_ID
✓ Bot should appear online in Discord within 10s
✓ If crash, check logs (auto-restart in 30s)
```

### Emails not drafting
```
✓ Check that Done/ folder has at least 1 email (for TF-IDF training)
✓ Verify ANTHROPIC_API_KEY is set
✓ Check email files have proper format (see draft_email SKILL)
```

### Research not generating
```
✓ Check GEMINI_API_KEY is set
✓ Verify Playwright installed: uv add playwright
✓ Check topic validity (BTC, AAPL, etc.)
```

### Todo not appearing in Dashboard
```
✓ Run: python -m src.todo_manager sync
✓ Check Dashboard.md exists at AI_Employee_Vault/Dashboard.md
✓ Verify todo.md has content
```

---

## 🎓 Code Examples

### Create Todo Programmatically
```python
from src.todo_manager import TodoManager

tm = TodoManager()
todo_id = tm.create_todo(
    title="Fix payment flow",
    priority="High",
    due_date="2026-03-10"
)
tm.sync_dashboard()
```

### Draft Email
```python
from src.automations.email_drafter import EmailDrafter

drafter = EmailDrafter()
draft = drafter.draft_reply({
    "subject": "Q1 Review",
    "sender": "manager@company.com",
    "body": "Can you send Q1 summary?",
    "context": "Quarterly planning"
})
drafter.save_draft(draft)
```

### Request Research
```python
from src.research_agent import ResearchAgent

agent = ResearchAgent()
results = agent.research_topics(["BTC", "AAPL"])
agent.save_report(results)
```

---

## 📞 Commands Quick Reference

```bash
# Todo Manager
zoya-todo create "Task Name" "High" "2026-03-15"
zoya-todo list
zoya-todo complete T001
zoya-todo sync

# Email Drafter
zoya-email-draft test
zoya-email-draft draft /path/to/email.md

# Research Agent
zoya-research --topics "BTC,AAPL" --dry-run
zoya-research --topics "BTC" --schedule "daily 09:00"

# Discord Bot
zoya-discord
```

---

## ✨ All Set!

**Time to Implementation**: ~15 minutes (install + configure + test)

**Ready to Deploy**: Yes, after .env configuration

**Full Documentation**: See PLATINUM_TIER_EXPANSION_COMPLETE.md

**Questions?** Check the SKILL.md files for detailed component instructions.

---

Created: 2026-03-07
Status: ✅ Ready for Testing
