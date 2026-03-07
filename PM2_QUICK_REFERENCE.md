# PM2 Quick Reference - Zoya Daemon Management

**Setup Date**: 2026-03-06
**Status**: Ready to deploy
**Last Updated**: 2026-03-06

---

## ⚡ 60-Second Setup

```bash
# 1. Install Node.js + PM2 (if needed)
bash scripts/pm2-setup.sh install

# 2. Start Zoya with PM2
bash scripts/pm2-setup.sh start

# 3. Enable auto-start on boot
bash scripts/pm2-setup.sh autostart

# Done! Zoya now runs forever ✓
```

---

## 🎮 Essential Commands

| Action | Command |
|--------|---------|
| **Start all services** | `bash scripts/pm2-setup.sh start` |
| **Check status** | `bash scripts/pm2-setup.sh status` |
| **View logs** | `bash scripts/pm2-setup.sh logs` |
| **Restart services** | `bash scripts/pm2-setup.sh restart` |
| **Stop services** | `bash scripts/pm2-setup.sh stop` |
| **Live monitoring** | `bash scripts/pm2-setup.sh monitor` |
| **Enable boot-time auto-start** | `bash scripts/pm2-setup.sh autostart` |

---

## 🔥 Direct PM2 Commands (If preferred)

```bash
# Status
pm2 status
pm2 show zoya-orchestrator

# Logs
pm2 logs                              # All services
pm2 logs zoya-orchestrator            # One service
pm2 logs zoya-orchestrator --err      # Error log only

# Control
pm2 restart all                       # Restart all
pm2 stop zoya-watcher                 # Stop one
pm2 restart zoya-gmail                # Restart one

# Monitoring
pm2 monit                             # Real-time dashboard
pm2 kill                              # Stop everything (clean reset)
```

---

## 📊 What's Running

```
Service              Purpose                        Memory Max
─────────────────────────────────────────────────────────────
zoya-watcher         File system monitoring         500 MB
zoya-gmail           Email polling                  400 MB
zoya-whatsapp        WhatsApp Web (Playwright)      800 MB
zoya-orchestrator    Main coordinator              600 MB
```

---

## 📁 Log Locations

```
AI_Employee_Vault/Logs/
├── pm2-watcher-out.log       ← stdout from file watcher
├── pm2-watcher-err.log       ← errors from file watcher
├── pm2-gmail-out.log         ← stdout from Gmail watcher
├── pm2-gmail-err.log         ← errors from Gmail watcher
├── pm2-whatsapp-out.log      ← stdout from WhatsApp watcher
├── pm2-whatsapp-err.log      ← errors from WhatsApp watcher
├── pm2-orchestrator-out.log  ← stdout from orchestrator
├── pm2-orchestrator-err.log  ← errors from orchestrator
├── 2026-03-06.log            ← Zoya app logs (all services)
└── 2026-03-06.json           ← Structured audit trail
```

---

## 🆘 Troubleshooting

### Services keep restarting

```bash
pm2 logs zoya-orchestrator --err
# Look for missing .env, invalid credentials, etc.
```

### High memory usage

```bash
pm2 monit
# If over limit → PM2 auto-restarts the process
# Edit ecosystem.config.js → max_memory_restart
```

### Can't start because port is in use

```bash
# Find what's using the port (e.g., 5001 for WhatsApp)
sudo lsof -i :5001
# Kill the process:
kill -9 <PID>
```

### Auto-start isn't working after reboot

```bash
pm2 save
pm2 startup
# Follow the printed instructions (usually a sudo command)
```

---

## ✅ Deployment Checklist

- [ ] Node.js installed: `node --version`
- [ ] PM2 installed: `pm2 --version`
- [ ] `.env` configured with all credentials
- [ ] Run: `bash scripts/pm2-setup.sh install`
- [ ] Run: `bash scripts/pm2-setup.sh start`
- [ ] Verify status: `pm2 status` (all 4 online)
- [ ] Test: Drop file in Inbox, monitor logs
- [ ] Run: `bash scripts/pm2-setup.sh autostart`
- [ ] Reboot and verify auto-start works

---

## 🚀 When Ready for Production

```bash
# Full automated setup
bash scripts/pm2-setup.sh install && \
bash scripts/pm2-setup.sh start && \
bash scripts/pm2-setup.sh autostart

# Verify
pm2 status

# Monitor in real-time
pm2 monit
```

---

## 📞 Files Reference

- **Config**: `ecosystem.config.js` - PM2 ecosystem config
- **Setup Guide**: `PM2_SETUP.md` - Detailed instructions
- **Helper Script**: `scripts/pm2-setup.sh` - Automation script
- **This File**: `PM2_QUICK_REFERENCE.md` - Quick commands

---

## 🎯 Before/After

### ❌ Before (Manual)
```
Terminal 1: uv run zoya-watcher
Terminal 2: uv run zoya-gmail
Terminal 3: uv run zoya-whatsapp
Terminal 4: uv run zoya-orchestrator
→ If crash: manual restart
→ If reboot: manual restart
```

### ✅ After (PM2)
```
bash scripts/pm2-setup.sh start
→ If crash: auto-restart
→ If reboot: auto-start
→ Monitor: pm2 monit
```

---

**Ready to deploy?** → `bash scripts/pm2-setup.sh install && bash scripts/pm2-setup.sh start` 🎉
