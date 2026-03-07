# 🚀 Quick Commands Reference

**Save this in your clipboard or bookmark it!**

---

## Instant Status Checks

```bash
# 1. Quick status (5 seconds - no API calls)
python quick_credential_status.py

# 2. Full validation (2 minutes - tests APIs)
python check_credentials.py

# 3. View latest report
cat CREDENTIAL_CHECK_REPORT.md
```

---

## Documentation (Read These)

```bash
# 0. README - Start here
cat CREDENTIAL_CHECKER_README.md

# 1. Quick summary & timeline
cat CREDENTIAL_SETUP_SUMMARY.md

# 2. Action plan with fix instructions (IMPORTANT!)
cat CREDENTIALS_ACTION_PLAN.md

# 3. Platform-specific reference
cat CREDENTIAL_VALIDATION_GUIDE.md

# 4. Full setup summary
cat CREDENTIAL_SETUP_SUMMARY.md
```

---

## LinkedIn Authentication (Playwright)

```bash
# 1. Login with email/password
python linkedin_playwright_login.py --method password --no-headless

# 2. Login with OAuth (manual browser)
python linkedin_playwright_login.py --method oauth --no-headless

# 3. Validate LinkedIn session
python linkedin_playwright_validator.py --browser --headless

# 4. Quick LinkedIn validation (no browser)
python linkedin_playwright_validator.py
```

---

## Full Automation

```bash
# Run everything at once
bash validate_all_credentials.sh

# This does:
# 1. Comprehensive credential check
# 2. LinkedIn-specific validation (if configured)
# 3. Generates report
```

---

## Fix Workflow

```bash
# Step 1: See what needs fixing
python quick_credential_status.py

# Step 2: Read detailed instructions
cat CREDENTIALS_ACTION_PLAN.md

# Step 3: For each credential, follow the action plan
# (Facebook → WhatsApp → LinkedIn → Twitter)

# Step 4: Re-validate after each fix
python check_credentials.py

# Step 5: Confirm health score ≥ 80% (goal: 100%)
cat CREDENTIAL_CHECK_REPORT.md
```

---

## Debugging

```bash
# Check what's actually in .env
grep -E "TWITTER|FACEBOOK|WHATSAPP|LINKEDIN" .env

# View full .env (be careful with secrets!)
cat .env

# Check which files were created
ls -la check_credentials.py linkedin_*.py quick_*.py

# View all documentation files
ls -la CREDENTIAL*.md
```

---

## Installation/Setup (First Time)

```bash
# Install required packages
pip install requests python-dotenv playwright

# Install Playwright browsers
playwright install chromium

# Make shell script executable
chmod +x validate_all_credentials.sh
```

---

## Daily/Weekly Checks

```bash
# Daily quick check (no API calls)
python quick_credential_status.py

# Weekly full validation
python check_credentials.py

# Monthly LinkedIn validation
python linkedin_playwright_validator.py --browser --headless
```

---

## Monitoring/Alerts

```bash
# Run and save to log
python check_credentials.py > credential_check_$(date +%Y%m%d).log

# Check if validation passed
if python check_credentials.py; then
  echo "✅ Credentials valid"
else
  echo "❌ Credentials invalid"
  # Send alert...
fi

# Parse health score
grep "Overall Health" CREDENTIAL_CHECK_REPORT.md
```

---

## Urgent Fixes

```bash
# If tokens expired:
# 1. Go to platform (Facebook, WhatsApp, LinkedIn, Twitter)
# 2. Generate new tokens
# 3. Update .env file
# 4. Run: python check_credentials.py

# If .env can't be found:
cd /media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150\ GB\ DATA\ TRANSFER/hackathon\ series/0\ FTE\ Hackathon/PIA-CLAUDE
python check_credentials.py

# If Playwright not installed:
pip install playwright
playwright install chromium
```

---

## Automation Examples

```bash
# Weekly cron job
0 0 * * 0 cd /path && python check_credentials.py >> credential_checks.log

# GitHub Actions
- name: Validate Credentials
  run: |
    python check_credentials.py
    grep "Overall Health: 100%" CREDENTIAL_CHECK_REPORT.md

# Docker
docker run -v $(pwd):/app python:3.10 bash -c "cd /app && pip install -r requirements.txt && python check_credentials.py"
```

---

## Quick Problem Solver

| Problem | Command |
|---------|---------|
| "What's configured?" | `python quick_credential_status.py` |
| "Are credentials working?" | `python check_credentials.py` |
| "Health score?" | `grep "Overall Health" CREDENTIAL_CHECK_REPORT.md` |
| "How do I fix this?" | `cat CREDENTIALS_ACTION_PLAN.md` |
| "LinkedIn not working?" | `python linkedin_playwright_login.py --method password --no-headless` |
| "Need help?" | `cat CREDENTIAL_CHECKER_README.md` |

---

## All Files at a Glance

```
🔧 Tools:
  check_credentials.py                 (Main validator - 450 lines)
  linkedin_playwright_login.py          (Browser auth - 280 lines)
  linkedin_playwright_validator.py      (Browser validator - 240 lines)
  quick_credential_status.py            (Quick check - 150 lines)
  validate_all_credentials.sh           (Bash wrapper - 100 lines)

📚 Docs:
  CREDENTIAL_CHECKER_README.md          (START HERE)
  CREDENTIALS_ACTION_PLAN.md            (DO THIS NEXT)
  CREDENTIAL_SETUP_SUMMARY.md           (Timeline)
  CREDENTIAL_VALIDATION_GUIDE.md        (Reference)
  QUICK_COMMANDS.md                     (This file)

📊 Reports:
  CREDENTIAL_CHECK_REPORT.md            (Latest results)
  SETUP_COMPLETE.txt                    (Installation summary)
```

---

**Pro Tip**: Bookmark this file and the action plan!
