#!/bin/bash

###############################################################################
# WhatsApp Watcher Setup Script
#
# This script sets up the WhatsApp Watcher system:
# 1. Installs required Python packages
# 2. Installs Playwright browsers
# 3. Creates vault folder structure
# 4. Creates configuration files
# 5. Verifies the setup
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}[*]${NC} $1"
}

# Main setup
print_header "WhatsApp Watcher Setup"

# Check Python
print_info "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.8 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"
echo ""

# Check if venv exists
if [ -d ".venv" ]; then
    print_warning ".venv directory already exists"
    read -p "Use existing virtual environment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing venv..."
        rm -rf .venv
    fi
fi

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"
echo ""

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip --quiet
print_success "pip upgraded"
echo ""

# Install Python packages
print_header "Installing Python Packages"

PACKAGES=(
    "playwright"
    "python-dotenv"
    "watchdog"
)

for package in "${PACKAGES[@]}"; do
    print_info "Installing $package..."
    pip install "$package" --quiet
    print_success "$package installed"
done
echo ""

# Install Playwright browsers
print_header "Installing Playwright Browsers"
print_info "Installing Chromium (this may take a minute)..."
python3 -m playwright install chromium
print_success "Chromium installed"
echo ""

# Create vault folder structure
print_header "Creating Vault Folder Structure"

VAULT_PATH="./AI_Employee_Vault"

# Create directories
DIRS=(
    "Needs_Action"
    "Plans"
    "Done"
    "Logs"
    "Pending_Approval"
    "Approved"
    "Rejected"
)

for dir in "${DIRS[@]}"; do
    DIR_PATH="$VAULT_PATH/$dir"
    if [ ! -d "$DIR_PATH" ]; then
        mkdir -p "$DIR_PATH"
        print_success "Created $DIR_PATH"
        # Add .gitkeep to track empty directories
        touch "$DIR_PATH/.gitkeep"
    else
        print_warning "$DIR_PATH already exists"
    fi
done
echo ""

# Create Dashboard.md if it doesn't exist
if [ ! -f "$VAULT_PATH/Dashboard.md" ]; then
    print_info "Creating Dashboard.md..."
    cat > "$VAULT_PATH/Dashboard.md" << 'EOF'
# WhatsApp Watcher Dashboard

## Status
- **Watcher Status**: [Not Started]
- **Last Check**: Never
- **Total Messages Processed**: 0
- **Pending Actions**: 0

## Recent Activity
*(Activity log appears here)*

## Quick Links
- [Pending Actions](Needs_Action)
- [Approved Messages](Approved)
- [Done Messages](Done)

---
*Last Updated: $(date)*
EOF
    print_success "Created Dashboard.md"
fi
echo ""

# Create .env file from example
print_header "Configuration Setup"

if [ ! -f ".env" ]; then
    print_info "Creating .env file..."
    cat > ".env" << 'EOF'
# WhatsApp Watcher Configuration

# Path to store WhatsApp Playwright session (relative or absolute)
WHATSAPP_WATCHER_SESSION_PATH=./whatsapp_session

# Path to your Obsidian vault
OBSIDIAN_VAULT_PATH=./AI_Employee_Vault

# Keywords to watch for in WhatsApp messages (comma-separated)
WHATSAPP_WATCHER_KEYWORDS=urgent,asap,invoice,payment,help,price,order,meeting,call me,contract

# Check interval in seconds (how often to scan for new messages)
WHATSAPP_WATCHER_CHECK_INTERVAL=30

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
WHATSAPP_WATCHER_LOG_LEVEL=INFO

# Dry run mode: if true, logs actions but doesn't create files
WHATSAPP_WATCHER_DRY_RUN=false

# Browser headless mode (false = visible window, useful for debugging)
WHATSAPP_WATCHER_BROWSER_HEADLESS=true

# Browser timeout in seconds (how long to wait for elements to load)
WHATSAPP_WATCHER_BROWSER_TIMEOUT=60
EOF
    print_success "Created .env file"
    print_warning "Please customize .env file with your preferences"
else
    print_warning ".env file already exists (skipping creation)"
fi
echo ""

# Verify installation
print_header "Verifying Installation"

print_info "Checking Playwright installation..."
python3 -c "from playwright.sync_api import sync_playwright; print('✓ Playwright OK')" && print_success "Playwright verified" || print_error "Playwright verification failed"

print_info "Checking python-dotenv installation..."
python3 -c "from dotenv import load_dotenv; print('✓ python-dotenv OK')" && print_success "python-dotenv verified" || print_error "python-dotenv verification failed"

print_info "Checking watchdog installation..."
python3 -c "from watchdog.observers import Observer; print('✓ watchdog OK')" && print_success "watchdog verified" || print_error "watchdog verification failed"
echo ""

# Final instructions
print_header "Setup Complete!"

echo "WhatsApp Watcher is now configured. Next steps:"
echo ""
echo "1. FIRST TIME SETUP ONLY - Run login script:"
echo "   ${BLUE}python3 first_login.py${NC}"
echo ""
echo "   This will:"
echo "   - Open a browser window (visible)"
echo "   - Load WhatsApp Web"
echo "   - Wait for you to scan the QR code"
echo "   - Save your session"
echo ""
echo "2. After login, start the watcher:"
echo "   ${BLUE}python3 orchestrator.py${NC}"
echo ""
echo "3. (Optional) Run in background with PM2:"
echo "   ${BLUE}npm install -g pm2  # if not already installed${NC}"
echo "   ${BLUE}pm2 start orchestrator.py --name 'whatsapp-watcher' -- --daemon${NC}"
echo ""
echo "4. (Optional) Customize keywords in .env:"
echo "   ${BLUE}nano .env${NC}"
echo ""
echo "For more details, see README.md"
echo ""
