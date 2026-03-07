# PM2 Setup Guide - Zoya Permanent Process Manager

**Status**: Ready to deploy
**Created**: 2026-03-06
**Tier**: Gold (with Platinum ready)

---

## 🚀 Quick Start (5 minutes)

### 1. Install PM2 Globally

```bash
npm install -g pm2
```

> If you don't have Node.js installed:
> ```bash
> curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
> sudo apt-get install -y nodejs
> ```

### 2. Start All Services

```bash
cd /path/to/PIA-CLAUDE
pm2 start ecosystem.config.js
```

**Output:**
```
[PM2] Spawning 4 processes...
┌─────┬──────────────────┬──────────┬──────┬─────────┬──────────┐
│ id  │ name             │ mode     │ ↺    │ status  │ cpu      │
├─────┼──────────────────┼──────────┼──────┼─────────┼──────────┤
│ 0   │ zoya-watcher     │ fork     │ 0    │ online  │ 0.5%     │
│ 1   │ zoya-gmail       │ fork     │ 0    │ online  │ 0.3%     │
│ 2   │ zoya-whatsapp    │ fork     │ 0    │ online  │ 1.2%     │
│ 3   │ zoya-orchestrator│ fork     │ 0    │ online  │ 0.8%     │
└─────┴──────────────────┴──────────┴──────┴─────────┴──────────┘
```

### 3. Verify Everything Works

```bash
# Check status
pm2 status

# View logs
pm2 logs

# Tail specific service
pm2 logs zoya-orchestrator
```

### 4. Enable Auto-Start on Boot (Linux/macOS)

```bash
pm2 save
pm2 startup

# Follow the instructions printed to terminal (usually one sudo command)
```

---

## 📋 Common Commands

### Monitoring

```bash
# Real-time dashboard
pm2 monit

# Show detailed info about all processes
pm2 show

# Show details for specific process
pm2 show zoya-watcher
```

### Log Management

```bash
# View all logs (streaming)
pm2 logs

# View specific service
pm2 logs zoya-orchestrator

# View last 100 lines
pm2 logs zoya-orchestrator --lines 100

# Clear all logs
pm2 flush
```

### Control

```bash
# Stop all services
pm2 stop all

# Restart all services
pm2 restart all

# Restart specific service
pm2 restart zoya-orchestrator

# Reload (graceful restart for 0-downtime)
pm2 reload all

# Stop and delete all processes
pm2 kill

# Delete specific process
pm2 delete zoya-watcher
```

---

## 🛡️ What PM2 Does For You

✅ **Auto-Restart**: Process crashes → automatic restart
✅ **Resource Limits**: Memory limit → auto-restart if exceeded
✅ **Log Rotation**: Automatic log file management
✅ **Boot Persistence**: `pm2 startup` + `pm2 save` = auto-start after reboot
✅ **Process Monitoring**: Watch CPU/memory in real-time
✅ **Graceful Shutdown**: Proper cleanup signals (SIGTERM → SIGKILL)

---

## 📊 Process Configuration Details

### Zoya-Watcher
- **Purpose**: Monitors `AI_Employee_Vault/Inbox/` for new files
- **Memory**: 500MB max
- **Restarts**: 10 max (prevents runaway restart loop)
- **Logs**: `AI_Employee_Vault/Logs/pm2-watcher-*.log`

### Zoya-Gmail
- **Purpose**: Polls Gmail for new emails
- **Memory**: 400MB max
- **Logs**: `AI_Employee_Vault/Logs/pm2-gmail-*.log`

### Zoya-WhatsApp
- **Purpose**: Monitors WhatsApp Web session (Playwright)
- **Memory**: 800MB max (Playwright uses more)
- **Logs**: `AI_Employee_Vault/Logs/pm2-whatsapp-*.log`

### Zoya-Orchestrator
- **Purpose**: Main coordinator (claims files, invokes Claude)
- **Memory**: 600MB max
- **Logs**: `AI_Employee_Vault/Logs/pm2-orchestrator-*.log`

---

## 🔧 Customization

### Change Memory Limits

Edit `ecosystem.config.js`:

```js
{
  name: 'zoya-orchestrator',
  // ...
  max_memory_restart: '1G', // Increase from 600M
}
```

Then restart:
```bash
pm2 restart ecosystem.config.js
```

### Change Log Location

Edit `ecosystem.config.js`:

```js
{
  name: 'zoya-watcher',
  out_file: '/var/log/zoya/watcher-out.log',
  error_file: '/var/log/zoya/watcher-err.log',
}
```

### Add Environment Variables

Edit `ecosystem.config.js`:

```js
{
  name: 'zoya-watcher',
  env: {
    NODE_ENV: 'production',
    PYTHONUNBUFFERED: '1',
    CUSTOM_VAR: 'value', // Add here
  }
}
```

---

## 🐛 Troubleshooting

### Process keeps restarting

```bash
# Check error logs
pm2 logs zoya-watcher --err

# Show restart count
pm2 show zoya-watcher
```

**Common causes:**
- Missing `.env` file
- Invalid credentials
- Port already in use

### Memory usage too high

```bash
# Check current memory
pm2 monit

# Increase limit in ecosystem.config.js
max_memory_restart: '1G'

# Restart
pm2 restart all
```

### Processes not starting on boot

```bash
# Re-run startup
pm2 startup

# Save current state
pm2 save

# Verify (will show startup command)
pm2 startup
```

### PM2 service not responding

```bash
# Kill all PM2 processes
pm2 kill

# Start fresh
pm2 start ecosystem.config.js
pm2 save
```

---

## 🚀 Production Deployment Checklist

- [ ] Node.js installed (`node --version`)
- [ ] PM2 installed globally (`pm2 --version`)
- [ ] `.env` file configured with all credentials
- [ ] Run `pm2 start ecosystem.config.js`
- [ ] Verify all 4 services are `online` status
- [ ] Run `pm2 monit` and check memory/CPU
- [ ] Test: drop a file in `AI_Employee_Vault/Inbox/`
- [ ] Monitor logs: `pm2 logs zoya-orchestrator`
- [ ] Once stable, run: `pm2 save && pm2 startup`
- [ ] Reboot and verify services auto-start

---

## 📝 Log Locations

All PM2 logs are written to:

```
AI_Employee_Vault/Logs/
├── pm2-watcher-out.log
├── pm2-watcher-err.log
├── pm2-gmail-out.log
├── pm2-gmail-err.log
├── pm2-whatsapp-out.log
├── pm2-whatsapp-err.log
├── pm2-orchestrator-out.log
├── pm2-orchestrator-err.log
├── 2026-03-06.log           # Zoya application logs
└── 2026-03-06.json          # Zoya structured logs
```

---

## 🔐 Security Notes

- **No hardcoded secrets** in `ecosystem.config.js`
- All credentials come from `.env` (gitignored)
- PM2 saves its state in `.pm2/` (add to `.gitignore` if not already)
- Logs contain no sensitive data (audit logs strip credentials)

---

## 🆚 Before/After Comparison

### Before (Manual bash)
```bash
# Terminal 1
uv run zoya-watcher

# Terminal 2
uv run zoya-gmail

# Terminal 3
uv run zoya-whatsapp

# Terminal 4
uv run zoya-orchestrator

# If any crashes → manual restart needed
# If machine reboots → manual restart needed
```

### After (PM2)
```bash
pm2 start ecosystem.config.js
# All 4 services start automatically
# Any crash → auto-restart
# Machine reboots → auto-start
# Monitor all with: pm2 monit
```

---

## 📞 Support

For PM2 issues:
```bash
pm2 diagnose

# Check PM2 logs
cat ~/.pm2/pm2.log

# Get help
pm2 help
pm2 help start
```

For Zoya-specific issues, check:
```bash
pm2 logs zoya-orchestrator --err
tail -f AI_Employee_Vault/Logs/$(date +%Y-%m-%d).json
```

---

## ✅ Ready to Deploy!

You're all set. Next step:

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

Then test by dropping a file in the Inbox. The system will keep running even if you close your terminal! 🎉
