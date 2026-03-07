# WhatsApp Watcher - Quick Start Guide

## 🚀 Complete Setup in 3 Commands

### Command 1: Install Everything
```bash
bash setup.sh
```

**What it does:**
- ✓ Creates Python virtual environment
- ✓ Installs Playwright, python-dotenv, watchdog
- ✓ Installs Chromium browser
- ✓ Creates vault folder structure
- ✓ Creates `.env` configuration file

**Time:** ~2 minutes

---

### Command 2: First-Time Login (ONE TIME ONLY)
```bash
python3 first_login.py
```

**What it does:**
1. Opens visible browser window
2. Loads WhatsApp Web
3. Shows QR code for 2 minutes
4. You scan with your phone
5. Saves session automatically
6. Browser closes

**What you do:**
1. Run the command above
2. **Open WhatsApp on your phone**
3. Go to: Settings → Linked Devices → Link a Device
4. **Scan the QR code** displayed in the browser
5. Wait for chat list to appear in browser (30-60 seconds)
6. Close the browser window

**Time:** ~2 minutes

**Important:** Only run this ONCE. Future runs will use the saved session.

---

### Command 3: Start the Watcher
```bash
python3 orchestrator.py
```

**Menu Options:**
```
[S] - Start watcher
[L] - List pending actions
[T] - Stop watcher
[Q] - Quit
```

**Type: S** then press Enter to start monitoring

**Time:** Starts immediately, runs indefinitely

---

## 📋 Complete Command Sequence

Copy-paste these commands in order:

```bash
# Step 1: Setup (takes ~2 min)
bash setup.sh

# Step 2: Verify everything is installed
python3 verify_setup.py

# Step 3: First login (takes ~2 min, DO THIS ONCE)
python3 first_login.py

# Step 4: Start watcher
python3 orchestrator.py

# In the menu that appears:
# Type "S" and press Enter to start watching
```

---

## ✅ How to Know It's Working

1. **Watcher Started**
   - You should see: `✓ WhatsApp Watcher started (running in background)`
   - Check interval: 30 seconds

2. **Send Test Message**
   - Open WhatsApp on phone
   - Send yourself a message: "urgent test"
   - Wait up to 60 seconds

3. **File Created**
   - Check folder: `AI_Employee_Vault/Needs_Action/`
   - You should see: `WHATSAPP_YYYYMMDD_HHMMSS_YourName.md`
   - File contains the message details with YAML frontmatter

4. **Logs**
   - Check: `AI_Employee_Vault/Logs/YYYY-MM-DD.json`
   - Should contain activity entries

---

## 🔧 Customizing Keywords

Edit `.env` file:

```bash
nano .env
```

Find this line:
```env
WHATSAPP_WATCHER_KEYWORDS=urgent,asap,invoice,payment,help,price,order,meeting,call me,contract
```

Replace with your keywords:
```env
WHATSAPP_WATCHER_KEYWORDS=invoice,payment,urgent,SOS,help
```

**Save:** Ctrl+O → Enter → Ctrl+X

**Restart watcher** for changes to take effect.

---

## 🌙 Running 24/7 with PM2

To keep the watcher running even after closing the terminal:

```bash
# Install PM2 (first time only)
npm install -g pm2

# Start watcher
pm2 start orchestrator.py --name 'whatsapp-watcher' -- --daemon

# Auto-start on boot
pm2 startup
pm2 save

# Check status
pm2 status

# View logs
pm2 logs whatsapp-watcher

# Stop watcher
pm2 stop whatsapp-watcher
```

---

## ⚠️ Troubleshooting

### "QR code not appearing"
```bash
# Clear session and try again
rm -rf whatsapp_session/
python3 first_login.py
```

### "Module not found" errors
```bash
# Rerun setup
bash setup.sh

# Or verify installation
python3 verify_setup.py
```

### "No files being created"
```bash
# Check logs
tail AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json

# Test with dry-run (doesn't create files, just logs)
# Edit .env and set: WHATSAPP_WATCHER_DRY_RUN=true
nano .env
python3 orchestrator.py
```

### "Watcher disconnects"
- WhatsApp session expires after ~7 days
- Re-login:
  ```bash
  rm -rf whatsapp_session/
  python3 first_login.py
  ```

---

## 📁 Files Created

**You will see:**
- `.env` - Configuration (customize this!)
- `.gitignore` - What to ignore in git
- `setup.sh` - Setup script
- `base_watcher.py` - Base class
- `whatsapp_watcher.py` - Main monitoring logic
- `first_login.py` - Login script
- `orchestrator.py` - Coordinator
- `verify_setup.py` - Verification script
- `WHATSAPP_WATCHER_README.md` - Full documentation

**Folders created automatically:**
- `whatsapp_session/` - Browser session storage
- `AI_Employee_Vault/Needs_Action/` - Action files appear here
- `AI_Employee_Vault/Logs/` - JSON logs

---

## 🎯 What Happens Next

1. **WhatsApp receives message** with keyword → Creates markdown file
2. **Claude Code monitors** `Needs_Action/` folder
3. **Reads the markdown file** with YAML frontmatter
4. **Processes the request** (reply, schedule task, etc.)
5. **Moves file** to `Done/` or `Approved/`

---

## 📚 More Information

**For detailed docs:**
```bash
cat WHATSAPP_WATCHER_README.md
```

**For troubleshooting:**
See "Troubleshooting" section in README.md

---

## 🆘 Quick Help

| Problem | Solution |
|---------|----------|
| QR code not showing | `rm -rf whatsapp_session/ && python3 first_login.py` |
| "Module not found" | `bash setup.sh` |
| No action files | Check `.env` keywords are correct |
| Watcher crashes | Check `AI_Employee_Vault/Logs/` for errors |
| Want to stop | Press `Ctrl+C` in terminal |

---

**Ready?** Start with:
```bash
bash setup.sh
```

Then follow the 3 commands above!
