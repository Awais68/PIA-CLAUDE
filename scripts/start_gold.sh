#!/usr/bin/env bash
# =============================================================
# Zoya Gold Tier — Start All Services
# =============================================================
# Launches: File Watcher + Gmail Watcher + WhatsApp Watcher +
#           Orchestrator + CEO Briefing (daily at 08:00)
# Usage:    ./scripts/start_gold.sh
# Stop:     Ctrl+C (graceful shutdown via trap)
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

PIDS=()

cleanup() {
    echo ""
    echo "[Zoya] Shutting down all services..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null || true
    echo "[Zoya] All services stopped."
}

trap cleanup EXIT INT TERM

echo "============================================"
echo "  Zoya Gold Tier — Starting Services"
echo "============================================"
echo ""

# Ensure Gold vault folders exist
echo "[Zoya] Initializing Gold vault folders..."
python3 -c "
from pathlib import Path
import src.config as cfg
for folder in [cfg.BRIEFINGS, cfg.CONTACTS]:
    folder.mkdir(parents=True, exist_ok=True)
    print(f'  OK: {folder}')
"

# 1. File System Watcher
echo "[Zoya] Starting File Watcher..."
uv run zoya-watcher &
PIDS+=($!)
echo "[Zoya] File Watcher started (PID ${PIDS[-1]})"

# 2. Gmail Watcher
echo "[Zoya] Starting Gmail Watcher..."
uv run zoya-gmail &
PIDS+=($!)
echo "[Zoya] Gmail Watcher started (PID ${PIDS[-1]})"

# 3. WhatsApp Watcher
echo "[Zoya] Starting WhatsApp Watcher (port 5001)..."
uv run zoya-whatsapp &
PIDS+=($!)
echo "[Zoya] WhatsApp Watcher started (PID ${PIDS[-1]})"

# 4. Orchestrator (Gold: includes Ralph loop + contact linker)
echo "[Zoya] Starting Gold Orchestrator..."
uv run zoya-orchestrator &
PIDS+=($!)
echo "[Zoya] Orchestrator started (PID ${PIDS[-1]})"

# 5. Generate initial daily briefing
echo "[Zoya] Generating initial daily briefing..."
uv run zoya-briefing && echo "[Zoya] Daily briefing generated." || echo "[Zoya] Briefing skipped."

echo ""
echo "============================================"
echo "  All services running. Press Ctrl+C to stop."
echo "============================================"
echo ""
echo "  File Watcher:      PID ${PIDS[0]}"
echo "  Gmail Watcher:     PID ${PIDS[1]}"
echo "  WhatsApp Watcher:  PID ${PIDS[2]}"
echo "  Orchestrator:      PID ${PIDS[3]}"
echo ""
echo "  Gold Features Active:"
echo "    ✓ CEO Briefing (zoya-briefing)"
echo "    ✓ Ralph Wiggum self-monitor (embedded in orchestrator)"
echo "    ✓ Contact Linker (embedded in orchestrator)"
echo "    ✓ Cross-domain priority routing"
echo ""
echo "  Add to crontab for automated briefings:"
echo "    0 8 * * *   cd $PROJECT_DIR && uv run zoya-briefing"
echo "    0 9 * * 1   cd $PROJECT_DIR && uv run zoya-briefing --weekly"
echo ""

# Wait for all background processes
wait
