# WhatsApp Watcher for Zoya AI Employee

A Playwright-based system that monitors WhatsApp Web for messages containing specific keywords and creates action files in your Obsidian vault for Claude Code to process.

## Features

✅ **Local WhatsApp Monitoring** - Uses Playwright to watch WhatsApp Web (not APIs)
✅ **Keyword Detection** - Filters messages by customizable keywords (urgent, invoice, payment, etc.)
✅ **Persistent Session** - Saves login session between runs
✅ **Action File Creation** - Creates markdown files in `/Needs_Action` folder
✅ **Duplicate Prevention** - Tracks processed messages to avoid duplicates
✅ **JSON Logging** - Full audit trail of all activities
✅ **Dry-Run Mode** - Test without creating files
✅ **Headless Operation** - Runs silently after first login
✅ **PM2 Ready** - Can run as always-on daemon service

## System Architecture

```
┌─────────────────────────────────────────┐
│     WhatsApp Web (via Playwright)       │
└──────────────┬──────────────────────────┘
               │ (monitors)
               ▼
┌─────────────────────────────────────────┐
│      WhatsAppWatcher (base_watcher)     │
│  - Checks every 30 seconds              │
│  - Extracts messages with keywords      │
│  - Tracks processed messages            │
└──────────────┬──────────────────────────┘
               │ (creates)
               ▼
┌─────────────────────────────────────────┐
│  Obsidian Vault / Needs_Action folder   │
│  - WHATSAPP_YYYYMMDD_HHMMSS_name.md    │
│  - Ready for Claude Code to process     │
└─────────────────────────────────────────┘
```

## Quick Start (5 minutes)

### 1. Run Setup Script
```bash
bash setup.sh
```

This will:
- Install Python packages (playwright, python-dotenv, watchdog)
- Install Playwright Chromium browser
- Create vault folder structure
- Create `.env` configuration file

### 2. First-Time Login (2 minutes)
```bash
python3 first_login.py
```

**What happens:**
1. Browser opens with WhatsApp Web
2. You see QR code
3. Scan with your phone's WhatsApp app
4. Session is saved automatically
5. Close the browser

### 3. Start the Watcher
```bash
python3 orchestrator.py
```

**In interactive mode, you can:**
- `[S]` Start watching
- `[L]` List pending actions
- `[T]` Stop watcher
- `[Q]` Quit

## File Structure

```
my_ai_employee/
├── .env                              # Configuration (create from .env.example)
├── .env.example                      # Configuration template
├── .gitignore                        # Git ignore rules
├── setup.sh                          # Setup script
├── README.md                         # This file
├── base_watcher.py                   # Abstract base class
├── whatsapp_watcher.py               # WhatsApp monitoring logic
├── first_login.py                    # Initial login script
├── orchestrator.py                   # Main coordinator
├── processed_ids.json                # (auto-created) Processed message IDs
├── whatsapp_session/                 # (auto-created) Browser session
│   └── state.json                    #  (auto-created) Session state
└── AI_Employee_Vault/
    ├── Needs_Action/                 # Action files appear here
    ├── Plans/
    ├── Done/
    ├── Logs/
    ├── Pending_Approval/
    ├── Approved/
    ├── Rejected/
    └── Dashboard.md
```

## Configuration (.env)

### Core Settings
```env
# Path to save WhatsApp browser session
WHATSAPP_WATCHER_SESSION_PATH=./whatsapp_session

# Path to your Obsidian vault
OBSIDIAN_VAULT_PATH=./AI_Employee_Vault

# Keywords to detect (comma-separated)
WHATSAPP_WATCHER_KEYWORDS=urgent,asap,invoice,payment,help,price,order,meeting,call me,contract

# How often to check for messages (seconds)
WHATSAPP_WATCHER_CHECK_INTERVAL=30
```

### Optional Settings
```env
# Run mode: true = visible, false = headless (default)
WHATSAPP_WATCHER_BROWSER_HEADLESS=true

# Page load timeout (seconds)
WHATSAPP_WATCHER_BROWSER_TIMEOUT=60

# Test mode: true = log but don't create files (default: false)
WHATSAPP_WATCHER_DRY_RUN=false

# Log level: DEBUG, INFO, WARNING, ERROR
WHATSAPP_WATCHER_LOG_LEVEL=INFO
```

### Customize Keywords

Edit `.env` and change the keywords:
```env
# Example: Monitor only financial keywords
WHATSAPP_WATCHER_KEYWORDS=invoice,payment,transfer,budget,expense

# Example: Add emotional keywords
WHATSAPP_WATCHER_KEYWORDS=urgent,asap,help,emergency,SOS
```

## Action File Format

When a message with keywords is detected, a markdown file is created in `/Needs_Action`:

**Filename**: `WHATSAPP_YYYYMMDD_HHMMSS_SenderName.md`

**Content**:
```markdown
---
type: whatsapp_message
from: Ahmed Khan
received: 2026-01-07T10:30:00
priority: high
status: pending
keywords_matched:
  - invoice
  - payment
---

## WhatsApp Message

**From:** Ahmed Khan
**Received:** 2026-01-07 10:30 AM

### Message Content
"Hey, can you send me the invoice for January? Payment is urgent."

### Keywords Detected
- invoice ✓
- payment ✓
- urgent ✓

## Suggested Actions
- [ ] Reply to sender
- [ ] Generate invoice if requested
- [ ] Create payment record
- [ ] Follow up if no response in 24 hours

## Draft Reply
*(Claude will fill this section)*

---
*Created by WhatsApp Watcher v1.0*
```

## Running the Watcher

### Interactive Mode
```bash
python3 orchestrator.py
```

Menu options:
```
[S] Start watcher        - Begin monitoring
[L] List pending actions - Show all action files
[T] Stop watcher        - Stop monitoring
[Q] Quit                - Exit program
```

### Daemon Mode (with PM2)

Install PM2 (first time only):
```bash
npm install -g pm2
```

Start watcher:
```bash
pm2 start orchestrator.py --name 'whatsapp-watcher' -- --daemon
```

Monitor logs:
```bash
pm2 logs whatsapp-watcher
```

Auto-start on reboot:
```bash
pm2 startup
pm2 save
```

Stop watcher:
```bash
pm2 stop whatsapp-watcher
```

### Dry-Run Mode (Testing)

Test without creating files:
```env
WHATSAPP_WATCHER_DRY_RUN=true
```

Then start:
```bash
python3 orchestrator.py
```

Output will show what WOULD happen without actually creating files.

## Logging

### JSON Logs
All activities are logged to `AI_Employee_Vault/Logs/YYYY-MM-DD.json`

Example log entry:
```json
{
  "timestamp": "2026-01-07T10:30:45.123456",
  "action_type": "whatsapp_message_detected",
  "actor": "whatsapp_watcher",
  "target": "Ahmed Khan",
  "parameters": {
    "keywords_matched": ["invoice", "payment", "urgent"],
    "message_preview": "Hey, can you send me the invoice..."
  },
  "result": "action_file_created"
}
```

### Console Output
Logs also appear in terminal with timestamps:
```
2026-01-07 10:30:45 - whatsapp_watcher - INFO - Found message from Ahmed Khan: ['invoice', 'payment']
```

## Troubleshooting

### QR Code Not Appearing

**Problem**: Browser opens but no QR code visible

**Solutions:**
1. Wait 5-10 seconds (takes time to load)
2. Refresh the page (press F5)
3. Clear browser cache:
   ```bash
   rm -rf whatsapp_session/
   python3 first_login.py
   ```
4. Check internet connection
5. Try another browser: Edit `whatsapp_watcher.py`, change `chromium` to `firefox`

### Session Expired

**Problem**: Watcher stops working, need to re-login

**Solutions:**
1. Verify you're still logged in on your phone
2. Delete session and re-login:
   ```bash
   rm -rf whatsapp_session/
   python3 first_login.py
   ```
3. Check browser timeout setting (increase if loading is slow):
   ```env
   WHATSAPP_WATCHER_BROWSER_TIMEOUT=120
   ```

### WhatsApp Not Loading

**Problem**: Page loads but chat list doesn't appear

**Solutions:**
1. Verify internet connection works
2. Try opening https://web.whatsapp.com in regular browser
3. Check your WhatsApp phone is connected to internet
4. Increase timeout:
   ```env
   WHATSAPP_WATCHER_BROWSER_TIMEOUT=120
   ```
5. Enable debug logging to see what's happening:
   ```env
   WHATSAPP_WATCHER_LOG_LEVEL=DEBUG
   ```

### Keywords Not Being Detected

**Problem**: Messages arrive but no action files created

**Debugging:**
1. Check keywords in `.env`:
   ```bash
   grep WHATSAPP_WATCHER_KEYWORDS .env
   ```
2. Keywords are case-insensitive (message is converted to lowercase)
3. Keywords must be complete words or phrases
4. Test with dry-run mode:
   ```env
   WHATSAPP_WATCHER_DRY_RUN=true
   WHATSAPP_WATCHER_LOG_LEVEL=DEBUG
   ```
5. Check logs:
   ```bash
   tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
   ```

### No Action Files Being Created

**Problem**: Watcher is running but no files appear in `/Needs_Action`

**Debugging:**
1. Check watcher is actually running:
   ```bash
   python3 orchestrator.py  # Select [L] to list actions
   ```
2. Verify vault path is correct:
   ```bash
   grep OBSIDIAN_VAULT_PATH .env
   ```
3. Check folder permissions:
   ```bash
   ls -la AI_Employee_Vault/Needs_Action/
   ```
4. Check logs for errors:
   ```bash
   tail AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json | grep error
   ```

### Watcher Using Too Much CPU

**Problem**: Watcher is slow or uses high CPU

**Solutions:**
1. Increase check interval (check less frequently):
   ```env
   WHATSAPP_WATCHER_CHECK_INTERVAL=60  # Check every 60 seconds
   ```
2. Close other browser windows
3. Check browser memory:
   - Run in headless mode (already default)
   - Restart periodically with cron job

### Permission Denied Errors

**Problem**: Error: Permission denied

**Solutions:**
1. Make setup script executable:
   ```bash
   chmod +x setup.sh
   ```
2. Make script executable:
   ```bash
   chmod +x orchestrator.py whatsapp_watcher.py first_login.py
   ```
3. Fix vault folder permissions:
   ```bash
   chmod -R 755 AI_Employee_Vault/
   ```

## Advanced Usage

### Custom Keyword Patterns

Use regex patterns for more flexible matching:

Edit `whatsapp_watcher.py` and modify `check_for_updates()`:
```python
import re
pattern = re.compile(r'(invoice|bill|payment)', re.IGNORECASE)
if pattern.search(message_text):
    # Create action file
```

### Integration with Claude Code

Claude Code will monitor the `/Needs_Action` folder and process files as they appear.

Example workflow:
1. **WhatsApp Watcher** detects: "Invoice #123 ready for review"
2. Creates file: `WHATSAPP_20260107_103000_Ahmed_Khan.md`
3. **Claude Code** reads file and:
   - Extracts invoice number
   - Retrieves PDF from system
   - Updates Odoo
   - Adds task to Obsidian

### Running Multiple Instances

Monitor different keywords separately:

**Instance 1** - Financial messages:
```env
WHATSAPP_WATCHER_KEYWORDS=invoice,payment,receipt
```
Start with: `python3 orchestrator.py`

**Instance 2** - Urgent messages:
```env
WHATSAPP_WATCHER_KEYWORDS=urgent,asap,emergency
```
Start with: `pm2 start orchestrator.py --name 'urgent-watcher'`

## Performance & Resource Usage

- **Memory**: ~60-120 MB (browser + Python)
- **CPU**: 1-5% (at rest, 10-15% during checks)
- **Disk**: ~50 MB (browser cache) + ~1 MB per 1000 messages
- **Network**: ~1 MB per 100 checks

## Maintenance

### Regular Tasks

**Weekly:**
```bash
# Clear old logs (keep last 30 days)
find AI_Employee_Vault/Logs -mtime +30 -delete

# Archive done files
mv AI_Employee_Vault/Done/* AI_Employee_Vault/Archive/ 2>/dev/null || true
```

**Monthly:**
```bash
# Clear browser cache
rm -rf whatsapp_session/
# Re-login
python3 first_login.py
```

### Check Health
```bash
# View last activity
tail -20 AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json

# Count pending actions
ls -1 AI_Employee_Vault/Needs_Action/ | wc -l

# Check watcher process
pm2 status whatsapp-watcher
```

## Security Notes

⚠️ **Important:**
- `.env` file contains session data - never commit to git
- `whatsapp_session/` folder contains browser authentication - keep safe
- Session tokens expire after ~7 days on new device - may require re-login
- WhatsApp Web limits logins - use same device for consistent login
- Don't delete `processed_ids.json` - tracks which messages were processed

## Limitations

- ❌ Cannot be used on multiple devices simultaneously (WhatsApp restriction)
- ❌ Cannot send messages (receive-only, use orchestrator for replies)
- ❌ Requires WhatsApp to be installed on your phone
- ❌ Session expires after ~7 days without activity
- ❌ Works only with WhatsApp (not WhatsApp Business API)

## License & Attribution

Part of Zoya Personal AI Employee project.

Powered by:
- [Playwright](https://playwright.dev) - Browser automation
- [python-dotenv](https://github.com/theskumar/python-dotenv) - Configuration
- [watchdog](https://github.com/gorakhargosh/watchdog) - File monitoring

## Support

For issues, check:
1. This README's Troubleshooting section
2. `.env` configuration is correct
3. Logs in `AI_Employee_Vault/Logs/`
4. Browser session still valid (re-login if needed)

---

**Last Updated**: 2026-03-02
**Version**: 1.0
