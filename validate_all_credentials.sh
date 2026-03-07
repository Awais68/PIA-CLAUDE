#!/bin/bash

###############################################################################
# Credential Validation Master Script
# Validates: WhatsApp, Facebook, Twitter, LinkedIn
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "================================================================================"
echo "🔐 CREDENTIAL VALIDATION SUITE"
echo "================================================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✅ Python 3 is available"

# Check if .env exists
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    echo "❌ .env file not found in ${SCRIPT_DIR}"
    exit 1
fi

echo "✅ .env file found"

# Activate virtual environment if it exists
if [ -d "${VENV_DIR}" ]; then
    echo "📦 Activating virtual environment..."
    source "${VENV_DIR}/bin/activate"
else
    echo "⚠️  Virtual environment not found at ${VENV_DIR}"
    echo "    Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

echo ""
echo "================================================================================"
echo "STEP 1: Comprehensive Credential Check"
echo "================================================================================"
echo ""

python3 "${SCRIPT_DIR}/check_credentials.py"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Credential check PASSED"
else
    echo ""
    echo "⚠️  Credential check returned warnings or errors"
    echo "   Review CREDENTIAL_CHECK_REPORT.md for details"
fi

echo ""
echo "================================================================================"
echo "STEP 2: LinkedIn-Specific Validation"
echo "================================================================================"
echo ""

if grep -q "LINKEDIN_ACCESS_TOKEN=" "${SCRIPT_DIR}/.env" && [ ! -z "$(grep 'LINKEDIN_ACCESS_TOKEN=' ${SCRIPT_DIR}/.env | cut -d= -f2 | xargs)" ]; then
    echo "📋 LinkedIn access token detected, running validation..."
    python3 "${SCRIPT_DIR}/linkedin_playwright_validator.py"
else
    echo "⏭️  LinkedIn access token not configured, skipping LinkedIn validation"
    echo ""
    echo "To set up LinkedIn:"
    echo "1. Add LINKEDIN_EMAIL and LINKEDIN_PASSWORD to .env"
    echo "2. Run: python3 ${SCRIPT_DIR}/linkedin_playwright_login.py --method password --no-headless"
fi

echo ""
echo "================================================================================"
echo "STEP 3: Summary"
echo "================================================================================"
echo ""

if [ -f "${SCRIPT_DIR}/CREDENTIAL_CHECK_REPORT.md" ]; then
    echo "📄 Report saved to: ${SCRIPT_DIR}/CREDENTIAL_CHECK_REPORT.md"
    echo ""
    echo "Report contents:"
    echo "---"
    cat "${SCRIPT_DIR}/CREDENTIAL_CHECK_REPORT.md"
    echo "---"
fi

echo ""
echo "================================================================================"
echo "✅ VALIDATION COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "1. Review the report above"
echo "2. Fix any invalid credentials (see CREDENTIAL_VALIDATION_GUIDE.md)"
echo "3. Re-run this script to verify fixes"
echo ""

exit 0
