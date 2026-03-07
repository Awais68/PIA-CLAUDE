# PM2 Deployment Summary - Zoya Production Setup

**Created**: 2026-03-06
**Status**: ✅ READY TO DEPLOY
**Effort**: 5 minutes to full production

---

## 📦 What Was Created

### 1. **`ecosystem.config.js`** (Core Configuration)
   - PM2 ecosystem configuration for all 4 Zoya services
   - Includes memory limits, auto-restart, log paths
   - Ready to use out-of-the-box

### 2. **`PM2_SETUP.md`** (Complete Guide)
   - 40+ page comprehensive setup documentation
   - Covers installation, commands, troubleshooting
   - Log locations, customization options
   - Production deployment checklist

### 3. **`scripts/pm2-setup.sh`** (Helper Script)
   - Automated installation and management script
   - Simple commands: `install`, `start`, `stop`, `restart`, `status`, `logs`, `monitor`, `autostart`
   - Handles all setup complexity

### 4. **`PM2_QUICK_REFERENCE.md`** (Quick Commands)
   - 1-page cheat sheet
   - Essential commands
   - Troubleshooting tips
   - Quick copy-paste reference

### 5. **`systemd-example.md`** (Alternative)
   - Linux-native alternative to PM2
   - Full service file templates
   - For those who prefer systemd over PM2

---

## 🚀 Quick Start (Choose One)

### Option A: Easiest (Recommended)

```bash
cd /path/to/PIA-CLAUDE
bash scripts/pm2-setup.sh install
bash scripts/pm2-setup.sh start
bash scripts/pm2-setup.sh autostart
```

**Done!** Zoya now runs forever. ✓

### Option B: Manual (More Control)

```bash
npm install -g pm2
cd /path/to/PIA-CLAUDE
pm2 start ecosystem.config.js
pm2 save
pm2 startup
# Follow printed instructions
```

### Option C: Linux systemd (Native)

See `systemd-example.md` for full instructions.

---

## ✅ What Happens After Setup

1. **All 4 services start automatically**
   - zoya-watcher (monitors Inbox)
   - zoya-gmail (polls Gmail)
   - zoya-whatsapp (monitors WhatsApp)
   - zoya-orchestrator (main coordinator)

2. **Auto-restart on crash**
   - If any service dies → PM2 restarts it in 10 seconds

3. **Auto-start on system reboot**
   - When machine reboots → services start automatically

4. **Real-time monitoring**
   - `pm2 monit` shows CPU/memory usage
   - `pm2 logs` shows all logs
   - `pm2 status` shows process states

---

## 📊 Services Configuration

| Service | Memory | Restarts | Purpose |
|---------|--------|----------|---------|
| zoya-watcher | 500MB | 10 max | Detects new files |
| zoya-gmail | 400MB | 10 max | Fetches emails |
| zoya-whatsapp | 800MB | 10 max | Monitors WhatsApp |
| zoya-orchestrator | 600MB | 10 max | Main coordinator |

---

## 🎯 Before vs After

### ❌ Before (Manual Terminal)
```
Terminal 1: uv run zoya-watcher
Terminal 2: uv run zoya-gmail
Terminal 3: uv run zoya-whatsapp
Terminal 4: uv run zoya-orchestrator

Problems:
• If you close terminal → services die
• If crash happens → manual restart needed
• If machine reboots → manual restart needed
• Hard to monitor multiple services
```

### ✅ After (PM2)
```
bash scripts/pm2-setup.sh start

Benefits:
• Services keep running even if terminal closes
• Crashes auto-restart automatically (10s)
• Machine reboot? Services auto-start
• Monitor all 4 in one place (pm2 monit)
```

---

## 🔧 Essential Commands Cheatsheet

```bash
# Installation & Setup
bash scripts/pm2-setup.sh install    # Install Node.js + PM2 if needed
bash scripts/pm2-setup.sh start      # Start all services

# Monitoring
bash scripts/pm2-setup.sh status     # Show status table
bash scripts/pm2-setup.sh monitor    # Real-time monitoring
bash scripts/pm2-setup.sh logs       # Tail all logs

# Control
bash scripts/pm2-setup.sh restart    # Restart all services
bash scripts/pm2-setup.sh stop       # Stop all services

# Persistence
bash scripts/pm2-setup.sh autostart  # Enable boot-time auto-start

# Direct PM2 (if preferred)
pm2 status
pm2 logs zoya-orchestrator
pm2 restart all
pm2 monit
```

---

## 📁 File Locations

```
Project Root/
├── ecosystem.config.js              ← PM2 config
├── PM2_SETUP.md                     ← Full guide
├── PM2_QUICK_REFERENCE.md           ← Cheat sheet
├── PM2_DEPLOYMENT_SUMMARY.md        ← This file
├── systemd-example.md               ← Systemd alternative
└── scripts/
    └── pm2-setup.sh                 ← Helper script (executable)

Logs/
├── AI_Employee_Vault/Logs/
│   ├── pm2-watcher-out.log
│   ├── pm2-watcher-err.log
│   ├── pm2-gmail-out.log
│   ├── pm2-gmail-err.log
│   ├── pm2-whatsapp-out.log
│   ├── pm2-whatsapp-err.log
│   ├── pm2-orchestrator-out.log
│   ├── pm2-orchestrator-err.log
│   ├── 2026-03-06.log              ← Zoya logs
│   └── 2026-03-06.json             ← Structured logs
```

---

## ✅ Pre-Deployment Checklist

- [ ] Node.js installed: `node --version` (v18+ recommended)
- [ ] `.env` file configured with all credentials
- [ ] All 4 services working when run manually
- [ ] Logs directory exists: `AI_Employee_Vault/Logs/`
- [ ] Have read access to project directory

---

## 🚀 Deployment Steps

### Step 1: Install (2 minutes)
```bash
bash scripts/pm2-setup.sh install
```

### Step 2: Start (1 minute)
```bash
bash scripts/pm2-setup.sh start
```

Verify with:
```bash
pm2 status
# All 4 should show "online" status
```

### Step 3: Test (2 minutes)
```bash
# Drop a test file
cp ~/Documents/test.pdf AI_Employee_Vault/Inbox/

# Watch it process
pm2 logs zoya-orchestrator

# Check result
cat AI_Employee_Vault/Done/FILE_*_test.md
```

### Step 4: Enable Auto-Start (1 minute)
```bash
bash scripts/pm2-setup.sh autostart
```

### Step 5: Reboot Test (Optional but Recommended)
```bash
sudo reboot

# After reboot, check:
pm2 status
# All 4 should show "online" status
```

**Total Time**: ~10 minutes to fully production-ready ✓

---

## 🔐 Security Notes

✅ No credentials in ecosystem.config.js
✅ All secrets from .env (gitignored)
✅ PM2 state files in .pm2/ (gitignored)
✅ Logs contain no sensitive data (audit trail)
✅ Process runs as your user (not root)

---

## 📞 Quick Troubleshooting

### Services won't start
```bash
# Check errors
pm2 logs --err
# Likely: missing .env or invalid credentials
```

### Memory usage too high
```bash
pm2 monit
# Edit ecosystem.config.js max_memory_restart
# Increase from 600M to 1G
```

### Auto-start not working
```bash
pm2 save
pm2 startup
# Follow printed instructions (usually one sudo command)
```

### Want to disable one service
```bash
pm2 stop zoya-gmail
pm2 delete zoya-gmail
```

---

## 🎓 Next Steps After Setup

1. **Monitor in production**
   ```bash
   pm2 monit
   ```

2. **Check logs regularly**
   ```bash
   pm2 logs | grep ERROR
   ```

3. **Upgrade when needed**
   ```bash
   pm2 reload ecosystem.config.js
   ```

4. **Scale to other machines** (cloud deployment)
   - Copy project to Oracle VM
   - Run `bash scripts/pm2-setup.sh install`
   - Run `bash scripts/pm2-setup.sh start`
   - Configure PM2 web dashboard: `pm2 web`

---

## 🏆 Production Ready Checklist

- [x] Ecosystem config created ✓
- [x] Helper script written ✓
- [x] Documentation complete ✓
- [x] Systemd alternative provided ✓
- [ ] Node.js installed ← **Your turn**
- [ ] Run setup script ← **Your turn**
- [ ] Enable auto-start ← **Your turn**
- [ ] Reboot and verify ← **Your turn**

---

## 📚 Reference Files

| File | Purpose |
|------|---------|
| `ecosystem.config.js` | PM2 config (ready to use) |
| `PM2_SETUP.md` | 40-page comprehensive guide |
| `PM2_QUICK_REFERENCE.md` | 1-page cheat sheet |
| `scripts/pm2-setup.sh` | Automated setup script |
| `systemd-example.md` | Linux systemd alternative |

---

## 🚀 Ready to Deploy?

**One command to rule them all:**

```bash
bash scripts/pm2-setup.sh install && \
bash scripts/pm2-setup.sh start && \
bash scripts/pm2-setup.sh autostart && \
pm2 status
```

Then verify logs are flowing:
```bash
pm2 logs zoya-orchestrator
```

**Congratulations!** Zoya is now in production. 🎉

---

**Questions?** Check:
1. `PM2_QUICK_REFERENCE.md` → Quick commands
2. `PM2_SETUP.md` → Detailed explanation
3. `scripts/pm2-setup.sh --help` → Script help

**Need systemd instead?** → `systemd-example.md`
