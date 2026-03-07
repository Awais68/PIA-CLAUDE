#!/bin/bash
# Install Playwright browser binaries
# Ensures chromium is available for LinkedIn and WhatsApp automation

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "🎭 Installing Playwright browsers..."

# Check if .venv exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "❌ Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Please run: uv venv first"
    exit 1
fi

# Activate venv and install browsers
cd "$PROJECT_ROOT"
source .venv/bin/activate

# Try installing with system dependencies first
echo "ℹ️ Installing chromium (attempt 1: with system dependencies)..."
if playwright install chromium --with-deps 2>/dev/null; then
    echo "✅ Installation with dependencies succeeded"
else
    echo "⚠️ Installation with --with-deps failed, trying without system deps..."
    echo "ℹ️ Installing chromium (attempt 2: without system dependencies)..."

    if playwright install chromium; then
        echo "✅ Chromium installed (system dependencies may need manual install)"
    else
        echo "❌ Failed to install chromium"
        echo "Try manually: .venv/bin/playwright install chromium"
        exit 1
    fi
fi

# Verify installation
echo ""
echo "🔍 Verifying installation..."

# Try to get browser path
BROWSER_CHECK=$(.venv/bin/python << 'EOF' 2>/dev/null
import sys
try:
    from playwright.async_api import async_playwright
    import asyncio
    import os

    async def check():
        try:
            pw = await async_playwright().start()
            # Try to launch to verify browser exists
            browser = await pw.chromium.launch()
            await browser.close()
            await pw.stop()
            print("✅")
            return 0
        except Exception as e:
            print(f"❌ {e}")
            return 1

    exit(asyncio.run(check()))
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
EOF
)

if [ "$BROWSER_CHECK" = "✅" ]; then
    echo "✅ Chromium verified and working!"
    echo ""
    echo "✨ Playwright setup complete!"
    echo ""
    echo "You can now run:"
    echo "  - python first_login_linkedin.py (for LinkedIn setup)"
    echo "  - python first_login.py (for WhatsApp setup)"
else
    echo "⚠️ Could not fully verify browser"
    echo "Try running: .venv/bin/playwright install chromium"
    exit 1
fi
