# Systemd Alternative Setup (Linux Only)

If you prefer **systemd** instead of PM2 (Linux-native, no Node.js required):

---

## Setup Instructions

### 1. Create Service Files

Create `/etc/systemd/system/zoya-*.service` files:

#### Zoya Watcher (`/etc/systemd/system/zoya-watcher.service`)

```ini
[Unit]
Description=Zoya File System Watcher
After=network.target
Wants=zoya-orchestrator.service

[Service]
Type=simple
User=awais
WorkingDirectory=/path/to/PIA-CLAUDE
ExecStart=/usr/bin/env uv run zoya-watcher
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

#### Zoya Gmail (`/etc/systemd/system/zoya-gmail.service`)

```ini
[Unit]
Description=Zoya Gmail Watcher
After=network.target
Wants=zoya-orchestrator.service

[Service]
Type=simple
User=awais
WorkingDirectory=/path/to/PIA-CLAUDE
ExecStart=/usr/bin/env uv run zoya-gmail
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

#### Zoya WhatsApp (`/etc/systemd/system/zoya-whatsapp.service`)

```ini
[Unit]
Description=Zoya WhatsApp Watcher
After=network.target
Wants=zoya-orchestrator.service

[Service]
Type=simple
User=awais
WorkingDirectory=/path/to/PIA-CLAUDE
ExecStart=/usr/bin/env uv run zoya-whatsapp
Restart=always
RestartSec=15
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

#### Zoya Orchestrator (`/etc/systemd/system/zoya-orchestrator.service`)

```ini
[Unit]
Description=Zoya Orchestrator (Main)
After=network.target zoya-watcher.service zoya-gmail.service

[Service]
Type=simple
User=awais
WorkingDirectory=/path/to/PIA-CLAUDE
ExecStart=/usr/bin/env uv run zoya-orchestrator
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
```

### 2. Install the Services

```bash
# Replace /path/to/PIA-CLAUDE with actual path first!

# Copy files to systemd
sudo cp /path/to/PIA-CLAUDE/zoya-*.service /etc/systemd/system/

# Reload systemd configuration
sudo systemctl daemon-reload

# Enable auto-start on boot
sudo systemctl enable zoya-watcher.service
sudo systemctl enable zoya-gmail.service
sudo systemctl enable zoya-whatsapp.service
sudo systemctl enable zoya-orchestrator.service
```

### 3. Start the Services

```bash
# Start all services
sudo systemctl start zoya-watcher.service
sudo systemctl start zoya-gmail.service
sudo systemctl start zoya-whatsapp.service
sudo systemctl start zoya-orchestrator.service

# Or start as a group:
sudo systemctl start zoya-*.service
```

### 4. Verify

```bash
# Check status
sudo systemctl status zoya-orchestrator.service

# View logs (real-time)
journalctl -u zoya-orchestrator.service -f

# View all Zoya logs
journalctl -u zoya-*.service -f
```

---

## Common Systemd Commands

```bash
# Start a service
sudo systemctl start zoya-watcher.service

# Stop a service
sudo systemctl stop zoya-orchestrator.service

# Restart a service
sudo systemctl restart zoya-orchestrator.service

# Enable auto-start
sudo systemctl enable zoya-watcher.service

# Disable auto-start
sudo systemctl disable zoya-watcher.service

# Check status
sudo systemctl status zoya-orchestrator.service

# View logs (last 50 lines)
journalctl -u zoya-orchestrator.service -n 50

# View logs (follow/tail)
journalctl -u zoya-orchestrator.service -f

# View logs since last boot
journalctl -u zoya-orchestrator.service -b

# View error logs only
journalctl -u zoya-orchestrator.service -p err
```

---

## Advantages

✅ **Linux-native** - No Node.js required
✅ **Simple** - Built into every Linux system
✅ **Reliable** - Systemd handles restart + dependencies
✅ **Integrated logging** - All logs in journalctl

---

## When to Use Systemd

- Linux-only (no macOS/Windows support)
- You want minimal dependencies
- You prefer standard Linux tooling
- No need for fancy dashboards

---

## When to Use PM2

- Cross-platform (macOS, Windows, Linux)
- Want web dashboard (`pm2 web`)
- More flexible configuration
- Cluster mode support (if needed later)

---

**Recommendation**: Start with **PM2** → simpler setup, works everywhere, can always switch to systemd later if needed.
