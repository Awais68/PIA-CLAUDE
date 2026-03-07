#!/usr/bin/env python3
"""
WhatsApp Watcher Setup Verification

Run this after setup.sh to verify everything is installed correctly.
"""

import sys
from pathlib import Path

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check(description):
    """Decorator for check functions."""
    def decorator(func):
        def wrapper():
            print(f"{BLUE}[*]{RESET} {description}...", end=" ", flush=True)
            try:
                result = func()
                if result:
                    print(f"{GREEN}✓{RESET}")
                    return True
                else:
                    print(f"{RED}✗{RESET}")
                    return False
            except Exception as e:
                print(f"{RED}✗ {e}{RESET}")
                return False
        return wrapper
    return decorator


print()
print("=" * 70)
print(f"{BLUE}WhatsApp Watcher Setup Verification{RESET}")
print("=" * 70)
print()

results = {}

# Check 1: Python version
@check("Python version >= 3.8")
def check_python():
    import sys
    return sys.version_info >= (3, 8)

results['python'] = check_python()

# Check 2: Python packages
@check("Playwright installed")
def check_playwright():
    from playwright.sync_api import sync_playwright
    return True

results['playwright'] = check_playwright()

@check("python-dotenv installed")
def check_dotenv():
    from dotenv import load_dotenv
    return True

results['dotenv'] = check_dotenv()

@check("watchdog installed")
def check_watchdog():
    from watchdog.observers import Observer
    return True

results['watchdog'] = check_watchdog()

# Check 3: Playwright browsers
@check("Chromium browser installed")
def check_chromium():
    from pathlib import Path
    chromium_path = Path.home() / ".cache" / "ms-playwright"
    return chromium_path.exists()

results['chromium'] = check_chromium()

print()

# Check 4: Configuration files
@check(".env file exists")
def check_env():
    return Path(".env").exists()

results['env'] = check_env()

@check(".env.example exists")
def check_env_example():
    return Path(".env.example").exists()

results['env_example'] = check_env_example()

@check(".gitignore exists")
def check_gitignore():
    return Path(".gitignore").exists()

results['gitignore'] = check_gitignore()

print()

# Check 5: Script files
@check("base_watcher.py exists")
def check_base_watcher():
    return Path("base_watcher.py").exists()

results['base_watcher'] = check_base_watcher()

@check("whatsapp_watcher.py exists")
def check_whatsapp_watcher():
    return Path("whatsapp_watcher.py").exists()

results['whatsapp_watcher'] = check_whatsapp_watcher()

@check("first_login.py exists")
def check_first_login():
    return Path("first_login.py").exists()

results['first_login'] = check_first_login()

@check("orchestrator.py exists")
def check_orchestrator():
    return Path("orchestrator.py").exists()

results['orchestrator'] = check_orchestrator()

print()

# Check 6: Vault structure
@check("Vault directory exists")
def check_vault():
    return Path("AI_Employee_Vault").is_dir()

results['vault'] = check_vault()

@check("Vault subdirectories exist")
def check_vault_subdirs():
    required = [
        "Needs_Action", "Plans", "Done", "Logs",
        "Pending_Approval", "Approved", "Rejected"
    ]
    vault = Path("AI_Employee_Vault")
    return all((vault / d).is_dir() for d in required)

results['vault_subdirs'] = check_vault_subdirs()

print()
print("=" * 70)

# Summary
passed = sum(1 for v in results.values() if v)
total = len(results)

if passed == total:
    print(f"{GREEN}✓ All checks passed! Ready to use.{RESET}")
    print()
    print("Next steps:")
    print(f"  1. {BLUE}python3 first_login.py{RESET}       (one-time login)")
    print(f"  2. {BLUE}python3 orchestrator.py{RESET}      (start watcher)")
    print()
    sys.exit(0)
else:
    print(f"{YELLOW}⚠ {total - passed} check(s) failed{RESET}")
    print()
    print("Failed items:")
    for name, result in results.items():
        if not result:
            print(f"  - {name}")
    print()
    print("Run setup again:")
    print(f"  {BLUE}bash setup.sh{RESET}")
    print()
    sys.exit(1)
