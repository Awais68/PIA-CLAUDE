# LinkedIn Automation - Quick Start Guide

## 🚀 Complete Setup in 5 Commands

### Command 1: Setup Folders & Templates (2 minutes)
```bash
bash linkedin_setup.sh
```

Creates:
- ✓ `/LinkedIn/Post_Queue/` — for posts to publish
- ✓ `/LinkedIn/Briefings/` — for weekly reports
- ✓ `/LinkedIn/Templates/` — reusable templates
- ✓ Template files (posts, DMs, business goals)

---

### Command 2: Configure Settings (5 minutes)
```bash
nano .env
```

These are the key settings to customize:
```env
LINKEDIN_SESSION_PATH=./linkedin_session
LINKEDIN_MAX_DAILY_ACTIONS=10
LINKEDIN_RUN_START_HOUR=8
LINKEDIN_RUN_END_HOUR=20
LINKEDIN_HASHTAGS=#Business #Entrepreneurship #Leadership
LINKEDIN_TARGET_INDUSTRIES=Business,Entrepreneurship,Leadership
LINKEDIN_DRY_RUN=false
```

**Save:** `Ctrl+O` → Enter → `Ctrl+X`

---

### Command 3: First-Time Login (2 minutes, RUN ONCE)
```bash
python3 first_login_linkedin.py
```

What happens:
1. Browser opens (visible window)
2. LinkedIn login page loads
3. You manually login to LinkedIn
4. Enter email, password, handle 2FA if needed
5. Feed loads automatically
6. Session is saved
7. Browser closes

**Do this ONCE. Future runs use saved session.**

---

### Command 4: Start Watcher (Monitor DMs & Comments)
```bash
python3 linkedin_watcher.py
```

Runs continuously:
- ✓ Checks DMs every 2 hours
- ✓ Checks comments every 3 hours
- ✓ Checks profile visitors daily
- ✓ Creates `.md` files in `/Needs_Action/`
- ✓ Stops at 8 PM (configured hours)

**You see:**
```
✓ LinkedIn Watcher started
  DM check interval: 7200s
  Comment check interval: 10800s
  Operating hours: 8:00 - 20:00
```

---

### Command 5: Start Poster (Auto-Post Approved Content)
```bash
python3 linkedin_poster.py
```

Runs continuously:
- ✓ Monitors `/LinkedIn/Post_Queue/` folder
- ✓ Checks every 30 minutes for approved posts
- ✓ Posts if: status=approved AND scheduled_time reached
- ✓ Types content character-by-character (human-like)
- ✓ Moves posted files to `/Done/`

**You see:**
```
✓ LinkedIn Poster started
  Queue path: ./AI_Employee_Vault/LinkedIn/Post_Queue
  Dry run: false
  Anti-detection: enabled
```

---

## 📋 Complete Command Sequence

Copy and paste:

```bash
# Step 1: Setup (2 min)
bash linkedin_setup.sh

# Step 2: Configure
nano .env
# (Edit the LinkedIn settings, then save)

# Step 3: First login (2 min, ONE TIME ONLY)
python3 first_login_linkedin.py

# Step 4: Start watcher (in terminal 1)
python3 linkedin_watcher.py

# Step 5: Start poster (in terminal 2, DIFFERENT TERMINAL)
python3 linkedin_poster.py

# Step 6: Generate weekly report (run Sunday evening)
python3 weekly_linkedin_report.py
```

**IMPORTANT:** Steps 4 & 5 run in separate terminals (they run continuously)

---

## ✅ How to Know It's Working

### DM Monitoring
1. Watcher is running
2. Someone sends you a DM on LinkedIn
3. Wait up to 2 hours for check (or restart watcher to check immediately)
4. Check folder: `AI_Employee_Vault/Needs_Action/`
5. You should see: `LINKEDIN_DM_YYYYMMDD_HHMMSS_SenderName.md`

### Comment Monitoring
1. Someone comments on your LinkedIn post
2. Wait up to 3 hours for check
3. Check folder: `AI_Employee_Vault/Needs_Action/`
4. You should see: `LINKEDIN_COMMENT_YYYYMMDD_HHMMSS_CommenterName.md`

### Auto-Posting
1. Create post in `/LinkedIn/Post_Queue/MY_POST.md`
2. Set status to `approved` (in YAML frontmatter)
3. Set `scheduled_time` to now or future
4. Wait up to 30 minutes (poster checks every 30 min)
5. Or restart poster to check immediately
6. Check logs: `tail AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json`
7. File should move to `/Done/` folder after posting

---

## 📝 How to Post Content

### 1. Create a Post
```bash
# Copy template
cp AI_Employee_Vault/LinkedIn/Templates/POST_TEMPLATE.md \
   AI_Employee_Vault/LinkedIn/Post_Queue/MY_POST_001.md
```

### 2. Edit the Post
```bash
nano AI_Employee_Vault/LinkedIn/Post_Queue/MY_POST_001.md
```

```markdown
---
scheduled_time: 2026-03-08T09:00:00
post_type: text
status: pending
approval_required: true
hashtags: #Business #Leadership #Innovation
language: English
---

Your amazing post content here!

Make it authentic and valuable for your audience.
```

### 3. Approve for Posting
Change `status: pending` to `status: approved`

### 4. Poster Automatically Posts
- When scheduled_time arrives
- And status is "approved"
- Watcher types it out char-by-char (human-like)
- File moves to `/Done/`

---

## 🎯 Key Points to Remember

### ✅ DO THIS
- ✅ Approve posts BEFORE posting (status=approved)
- ✅ Use templates as starting point
- ✅ Keep posts authentic and valuable
- ✅ Check `/Needs_Action/` folder for DMs/comments
- ✅ Review logs regularly
- ✅ Run weekly report every Sunday

### ❌ DON'T DO THIS
- ❌ Don't post without approval
- ❌ Don't spam or post constantly
- ❌ Don't change watcher while running
- ❌ Don't delete `processed_ids.json` (tracks seen messages)
- ❌ Don't share your `.env` file (contains session)

---

## 📁 File Organization

```
Create posts here:
AI_Employee_Vault/LinkedIn/Post_Queue/MY_POST_001.md
              ↓ (after approval & posting) ↓
              AI_Employee_Vault/Done/MY_POST_001.md

Read DMs/comments here:
AI_Employee_Vault/Needs_Action/LINKEDIN_DM_*.md
AI_Employee_Vault/Needs_Action/LINKEDIN_COMMENT_*.md

Find templates here:
AI_Employee_Vault/LinkedIn/Templates/
  ├── POST_TEMPLATE.md
  ├── DM_TEMPLATES.md
  └── Business_Goals.md

Weekly reports here:
AI_Employee_Vault/Briefings/LINKEDIN_WEEKLY_*.md

Logs here:
AI_Employee_Vault/Logs/YYYY-MM-DD.json
```

---

## 🔧 Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| "Need to login again" | `python3 first_login_linkedin.py` |
| "No DMs detected" | Check if between 8 AM - 8 PM, check logs |
| "Posts not publishing" | Make sure status=approved in YAML |
| "Session expired" | Delete `./linkedin_session/` and re-login |
| "Watcher not running" | Check if Python is available: `python3 --version` |
| "Can't create folders" | Check permissions: `ls -la AI_Employee_Vault/` |

---

## 🌙 Running 24/7 (Optional - PM2)

To keep watcher & poster running all the time:

```bash
# Install PM2 (first time only)
npm install -g pm2

# Start both services
pm2 start linkedin_watcher.py --name "linkedin-watcher"
pm2 start linkedin_poster.py --name "linkedin-poster"

# Auto-start on reboot
pm2 startup
pm2 save

# Check status
pm2 status

# View logs
pm2 logs linkedin-watcher
pm2 logs linkedin-poster

# Stop if needed
pm2 stop linkedin-watcher
pm2 stop linkedin-poster
```

---

## 📊 Monitoring

### Check Pending Items
```bash
# DMs and comments waiting for review
ls -la AI_Employee_Vault/Needs_Action/LINKEDIN_*.md
```

### View Activity Logs
```bash
# Today's activity
cat AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq .

# Last 5 entries
tail -5 AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | jq .
```

### Generate Report
```bash
# Create weekly report
python3 weekly_linkedin_report.py

# View report
cat AI_Employee_Vault/Briefings/LINKEDIN_WEEKLY_*.md
```

---

## ⚠️ Important Notes

### Safety
- **No automatic posting without approval** - Must set status=approved
- **No automatic replies** - DMs create files for human review
- **Daily limit** - Max 10 actions per day (prevents detection)
- **Operating hours** - Only runs 8 AM - 8 PM (natural behavior)

### Limits
- Post max: 3000 characters
- Check intervals: 2h (DMs), 3h (comments), 24h (visitors)
- Free account: Limited profile visitor access (90 days)
- Session expires: ~7 days (may need re-login)

---

## 🎓 Advanced Features

### Dry-Run Mode (Test First)
```env
LINKEDIN_DRY_RUN=true
```

Logs what WOULD happen without actually posting. Useful for testing!

### Debug Logging
```env
LINKEDIN_LOG_LEVEL=DEBUG
```

Shows detailed information for troubleshooting.

### Customize Check Intervals
```env
LINKEDIN_CHECK_INTERVAL_DM=3600        # Check DMs every hour
LINKEDIN_CHECK_INTERVAL_COMMENTS=5400  # Check comments every 90 min
```

### Anti-Detection Tuning
```env
LINKEDIN_ENABLE_ANTI_DETECTION=true    # Random delays
LINKEDIN_RUN_START_HOUR=8              # Start time
LINKEDIN_RUN_END_HOUR=20               # End time
```

---

## 📚 Full Documentation

For detailed information, see:
- `LINKEDIN_AUTOMATION_README.md` — Complete guide
- `.env.example` — All configuration options
- `linkedin_watcher.py` — Source code with docstrings
- `linkedin_poster.py` — Source code with docstrings

---

## 🆘 Need Help?

1. **Check the logs:**
   ```bash
   tail AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
   ```

2. **Enable debug:**
   ```env
   LINKEDIN_LOG_LEVEL=DEBUG
   ```

3. **Test with dry-run:**
   ```env
   LINKEDIN_DRY_RUN=true
   ```

4. **Read the README:**
   ```bash
   cat LINKEDIN_AUTOMATION_README.md | less
   ```

---

## ✨ You're Ready!

Everything is set up. Just:

1. Run `bash linkedin_setup.sh`
2. Edit `.env`
3. Run `python3 first_login_linkedin.py` (once)
4. Run `python3 linkedin_watcher.py` (terminal 1)
5. Run `python3 linkedin_poster.py` (terminal 2)

Your LinkedIn automation is now active! 🚀

---

**Built for Zoya Personal AI Employee | Claude Code Hackathon**

Questions? Check LINKEDIN_AUTOMATION_README.md for detailed answers!
