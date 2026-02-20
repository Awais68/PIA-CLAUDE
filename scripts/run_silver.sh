#!/usr/bin/env bash
# ================================================================
# Zoya Silver — One-Command Runner
# Usage:  ./scripts/run_silver.sh
# ================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VAULT="$PROJECT_DIR/AI_Employee_Vault"
PIDS=()

# ----------------------------------------------------------------
# Colours
# ----------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}[  OK]${RESET}  $*"; }
info() { echo -e "${CYAN}[INFO]${RESET}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
head() { echo -e "\n${BOLD}$*${RESET}"; }

# ----------------------------------------------------------------
# Cleanup on Ctrl+C / exit
# ----------------------------------------------------------------
cleanup() {
    echo ""
    info "Shutting down all services..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null || true
    ok "All stopped. Logs: /tmp/zoya_*.log"
}
trap cleanup EXIT INT TERM

cd "$PROJECT_DIR"

# ================================================================
head "═══════════════════════════════════════════"
echo -e "  ${BOLD}Zoya Silver Tier — Auto Runner${RESET}"
head "═══════════════════════════════════════════"

# ----------------------------------------------------------------
# 1. Quick dependency check
# ----------------------------------------------------------------
head "Step 1/5 — Checking dependencies"
uv sync --quiet && ok "uv dependencies ready"

# ----------------------------------------------------------------
# 2. Start services
# ----------------------------------------------------------------
head "Step 2/5 — Starting services"

uv run zoya-watcher > /tmp/zoya_watcher.log 2>&1 &
PIDS+=($!)
ok "File Watcher started    (PID ${PIDS[-1]})  log: /tmp/zoya_watcher.log"

uv run zoya-whatsapp > /tmp/zoya_whatsapp.log 2>&1 &
PIDS+=($!)
ok "WhatsApp Watcher started (PID ${PIDS[-1]})  log: /tmp/zoya_whatsapp.log"
sleep 2   # give Flask time to bind port

uv run zoya-orchestrator > /tmp/zoya_orchestrator.log 2>&1 &
PIDS+=($!)
ok "Orchestrator started    (PID ${PIDS[-1]})  log: /tmp/zoya_orchestrator.log"
sleep 1

# ----------------------------------------------------------------
# 3. Health check
# ----------------------------------------------------------------
head "Step 3/5 — Health check"

HEALTH=$(curl -s http://localhost:5001/health 2>/dev/null || echo "")
if echo "$HEALTH" | grep -q '"running":true'; then
    ok "WhatsApp webhook  → http://localhost:5001/health"
else
    warn "WhatsApp webhook not ready yet (may still be starting)"
fi

RALPH=$(uv run python3 -c "
from src.ralph_loop import get_system_status
s = get_system_status()
print(s['status'])
" 2>/dev/null || echo "unknown")
if [ "$RALPH" = "ok" ]; then
    ok "Ralph self-monitor → status: OK"
else
    warn "Ralph status: $RALPH"
fi

# ----------------------------------------------------------------
# 4. Live demo — drop a test file
# ----------------------------------------------------------------
head "Step 4/5 — Dropping demo file into Inbox"

DEMO_FILE="$VAULT/Inbox/demo_contract.md"
cat > "$DEMO_FILE" << 'MDEOF'
# Service Contract — TechCorp & Zoya Corp

**Date:** 2026-02-18
**Parties:** TechCorp Ltd (Client) and Zoya Corp (Provider)
**Value:** $12,500

## Scope of Work
- Phase 1: AI pipeline setup (due March 15)
- Phase 2: Integration testing (due April 1)
- Phase 3: Production deployment (due April 30)

## Payment Terms
- 30% on signing: $3,750 — due immediately
- 40% on Phase 2 completion: $5,000
- 30% on final delivery: $3,750

## Action Required
- [ ] Sign and return by Feb 25
- [ ] First payment due Feb 28
- [ ] Kick-off meeting March 1
MDEOF

ok "Demo contract dropped → $DEMO_FILE"
info "Waiting for watcher to pick it up..."

# Wait up to 8 seconds for watcher to queue it
for i in $(seq 1 8); do
    sleep 1
    if ls "$VAULT/Needs_Action/"FILE_*_demo_contract.md 2>/dev/null | grep -q demo_contract; then
        ok "Watcher queued it in Needs_Action/ (${i}s)"
        break
    fi
done

# ----------------------------------------------------------------
# 5. Send a test WhatsApp message
# ----------------------------------------------------------------
head "Step 5/5 — Sending test WhatsApp message"

WA_RESP=$(curl -s -X POST http://localhost:5001/test-message \
    -H "Content-Type: application/json" \
    -d '{"from": "+923001234567", "message": "Hi, please check the contract I just sent. Deadline is Feb 25!", "type": "text"}' \
    2>/dev/null || echo "")

if echo "$WA_RESP" | grep -q '"status":"queued"'; then
    ok "WhatsApp message queued from +923001234567"
else
    warn "WhatsApp test message failed (watcher may still be starting)"
fi

# ----------------------------------------------------------------
# Summary
# ----------------------------------------------------------------
head "═══════════════════════════════════════════"
echo -e "  ${GREEN}${BOLD}All systems running!${RESET}"
head "═══════════════════════════════════════════"
echo ""
echo -e "  ${CYAN}Services:${RESET}"
echo "    File Watcher     PID ${PIDS[0]}"
echo "    WhatsApp Watcher PID ${PIDS[1]}  → http://localhost:5001"
echo "    Orchestrator     PID ${PIDS[2]}"
echo ""
echo -e "  ${CYAN}Now test it yourself:${RESET}"
echo ""
echo -e "  ${BOLD}1. Drop any PDF/MD/DOCX into Inbox:${RESET}"
echo "     cp ~/Documents/any.pdf \"$VAULT/Inbox/\""
echo ""
echo -e "  ${BOLD}2. Watch the queue live:${RESET}"
echo "     watch -n 2 'ls \"$VAULT/Needs_Action/\" \"$VAULT/Done/\"'"
echo ""
echo -e "  ${BOLD}3. Send a WhatsApp test message:${RESET}"
echo "     curl -X POST http://localhost:5001/test-message \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"from\":\"+923001234567\",\"message\":\"test msg\",\"type\":\"text\"}'"
echo ""
echo -e "  ${BOLD}4. Force process queue now:${RESET}"
echo "     uv run zoya-orchestrator --once"
echo ""
echo -e "  ${BOLD}5. Generate CEO briefing:${RESET}"
echo "     uv run zoya-briefing"
echo ""
echo -e "  ${BOLD}6. Check Dashboard:${RESET}"
echo "     cat \"$VAULT/Dashboard.md\""
echo ""
echo -e "  ${BOLD}7. Follow live logs:${RESET}"
echo "     tail -f \"$VAULT/Logs/\$(date +%Y-%m-%d).log\""
echo ""
echo -e "  ${BOLD}8. Full test guide:${RESET}  cat silver_start.md"
echo ""
echo -e "  ${YELLOW}Press Ctrl+C to stop all services.${RESET}"
echo ""

# Keep alive
wait
