#!/usr/bin/env bash
# =============================================================
# Zoya Silver Tier — Start All Services
# =============================================================
# Launches: File Watcher + Gmail Watcher + Orchestrator
# Usage:    ./scripts/start_silver.sh
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
echo "  Zoya Silver Tier — Starting Services"
echo "============================================"
echo ""

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
echo "[Zoya] Starting WhatsApp Watcher..."
uv run zoya-whatsapp &
PIDS+=($!)
echo "[Zoya] WhatsApp Watcher started (PID ${PIDS[-1]})"

# 4. Orchestrator
echo "[Zoya] Starting Orchestrator..."
uv run zoya-orchestrator &
PIDS+=($!)
echo "[Zoya] Orchestrator started (PID ${PIDS[-1]})"

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

# Wait for all background processes
wait
