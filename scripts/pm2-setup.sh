#!/usr/bin/env bash
# =============================================================
# PM2 Setup & Management Script
# Automates installation, startup, and persistence
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if Node.js is installed
check_nodejs() {
    print_header "Checking Node.js"

    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js installed: $NODE_VERSION"
        return 0
    else
        print_error "Node.js not found"
        echo ""
        echo "Install Node.js with:"
        echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        echo "  sudo apt-get install -y nodejs"
        echo ""
        exit 1
    fi
}

# Check if PM2 is installed
check_pm2() {
    print_header "Checking PM2"

    if command -v pm2 &> /dev/null; then
        PM2_VERSION=$(pm2 --version)
        print_success "PM2 installed: $PM2_VERSION"
        return 0
    else
        print_info "PM2 not found, installing globally..."
        npm install -g pm2 || {
            print_error "Failed to install PM2"
            exit 1
        }
        print_success "PM2 installed"
    fi
}

# Start all services
start_services() {
    print_header "Starting Zoya Services"

    cd "$PROJECT_DIR"

    print_info "Using ecosystem config: ecosystem.config.js"
    pm2 start ecosystem.config.js

    echo ""
    pm2 status
    echo ""
    print_success "All services started!"
}

# Show status
show_status() {
    print_header "Zoya Service Status"
    pm2 status
    echo ""
    print_info "Tip: Use 'pm2 monit' for real-time monitoring"
}

# Show logs
show_logs() {
    print_header "Zoya Service Logs"
    pm2 logs
}

# Enable auto-start on boot
enable_autostart() {
    print_header "Enabling Auto-Start on Boot"

    pm2 save || {
        print_error "Failed to save PM2 state"
        return 1
    }
    print_success "PM2 state saved"

    print_info "Running: pm2 startup"
    pm2 startup || {
        print_error "Failed to setup startup"
        return 1
    }

    echo ""
    print_success "Auto-start enabled!"
    print_info "Services will restart automatically on system reboot"
}

# Stop all services
stop_services() {
    print_header "Stopping Zoya Services"
    pm2 stop all
    print_success "All services stopped"
}

# Restart all services
restart_services() {
    print_header "Restarting Zoya Services"
    pm2 restart all
    echo ""
    pm2 status
    print_success "All services restarted"
}

# Show help
show_help() {
    cat << 'EOF'
Usage: ./pm2-setup.sh [COMMAND]

Commands:
  install      Check/install Node.js and PM2
  start        Start all Zoya services
  stop         Stop all Zoya services
  restart      Restart all Zoya services
  status       Show service status
  logs         Tail service logs
  monitor      Real-time monitoring (pm2 monit)
  autostart    Enable auto-start on boot
  diagnose     Run PM2 diagnostics
  help         Show this help message

Examples:
  ./pm2-setup.sh install    # First time setup
  ./pm2-setup.sh start      # Start services
  ./pm2-setup.sh status     # Check status
  ./pm2-setup.sh logs       # View logs
  ./pm2-setup.sh autostart  # Enable boot-time startup

Quick Start:
  ./pm2-setup.sh install
  ./pm2-setup.sh start
  ./pm2-setup.sh autostart
EOF
}

# Main
main() {
    COMMAND="${1:-help}"

    case "$COMMAND" in
        install)
            check_nodejs
            check_pm2
            print_success "Installation check complete!"
            ;;
        start)
            check_nodejs
            check_pm2
            start_services
            ;;
        stop)
            check_pm2
            stop_services
            ;;
        restart)
            check_pm2
            restart_services
            ;;
        status)
            check_pm2
            show_status
            ;;
        logs)
            check_pm2
            show_logs
            ;;
        monitor)
            check_pm2
            pm2 monit
            ;;
        autostart)
            check_pm2
            enable_autostart
            ;;
        diagnose)
            check_pm2
            pm2 diagnose
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main
main "$@"
