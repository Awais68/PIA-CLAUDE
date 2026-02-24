#!/usr/bin/env bash
# =============================================================
# Zoya Live Status Monitor
# Shows real-time activity from all running services
# =============================================================

cat << 'EOF'

╔══════════════════════════════════════════════════════════════════╗
║           ✨ ZOYA - LIVE STATUS DASHBOARD ✨                    ║
╚══════════════════════════════════════════════════════════════════╝

EOF

echo "📊 RUNNING SERVICES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pgrep -a -f "zoya-watcher" | head -1 && echo "  ✓ File Watcher      - Monitoring /Inbox/" || echo "  ✗ File Watcher      - Not running"
pgrep -a -f "zoya-gmail" | head -1 && echo "  ✓ Gmail Watcher     - Polling Gmail inbox" || echo "  ✗ Gmail Watcher     - Not running"
pgrep -a -f "zoya-whatsapp" | head -1 && echo "  ✓ WhatsApp Watcher  - Running on port 5001" || echo "  ✗ WhatsApp Watcher  - Not running"
pgrep -a -f "zoya-orchestrator" | head -1 && echo "  ✓ Orchestrator      - Processing queue" || echo "  ✗ Orchestrator      - Not running"
pgrep -a -f "zoya-social-daemon" | head -1 && echo "  ✓ Social Daemon     - Twitter & LinkedIn automation" || echo "  ✗ Social Daemon     - Not running"
echo ""

echo "📊 VAULT STATS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
VAULT="/media/awais/6372445e-8fda-42fa-9034-61babd7dafd1/150 GB DATA TRANSFER/hackathon series/0 FTE Hackathon/PIA-CLAUDE/AI_Employee_Vault"
echo "  📥 Inbox:            $(ls -1 "$VAULT/Inbox" 2>/dev/null | wc -l) files"
echo "  ⏳ Needs Action:     $(ls -1 "$VAULT/Needs_Action" 2>/dev/null | wc -l) files"
echo "  ⚙️  In Progress:      $(ls -1 "$VAULT/In_Progress" 2>/dev/null | wc -l) files"
echo "  ✅ Done:             $(ls -1 "$VAULT/Done" 2>/dev/null | wc -l) files"
echo "  🔍 Pending Approval: $(ls -1 "$VAULT/Pending_Approval" 2>/dev/null | wc -l) files"
echo "  ✅ Approved:         $(ls -1 "$VAULT/Approved" 2>/dev/null | wc -l) files"
echo ""

echo "📱 SOCIAL MEDIA STATUS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f /tmp/zoya_social_daemon.log ]; then
    tail -10 /tmp/zoya_social_daemon.log | grep -E "INFO|Cycle|Creating|Posted|approval" || echo "  Waiting for activity..."
else
    echo "  Social daemon log not found"
fi
echo ""

echo "📝 RECENT LOGS (Last 5 lines each):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f /tmp/zoya_orchestrator.log ]; then
    echo "⚙️  Orchestrator:"
    tail -5 /tmp/zoya_orchestrator.log | sed 's/^/    /'
    echo ""
fi

if [ -f /tmp/zoya_gmail_watcher.log ]; then
    echo "📧 Gmail:"
    tail -5 /tmp/zoya_gmail_watcher.log | sed 's/^/    /'
    echo ""
fi

if [ -f /tmp/zoya_whatsapp_watcher.log ]; then
    echo "💬 WhatsApp:"
    tail -5 /tmp/zoya_whatsapp_watcher.log | sed 's/^/    /'
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 TIP: Run 'watch -n 5 ./scripts/live_status.sh' for auto-refresh"
echo "📊 Log files: /tmp/zoya_*.log"
echo ""
