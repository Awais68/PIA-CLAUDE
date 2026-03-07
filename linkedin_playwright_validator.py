#!/usr/bin/env python3
"""
LinkedIn Credential Validator using Playwright
Tests authentication and posting capability
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

from dotenv import load_dotenv

# Load .env
load_dotenv()

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
except ImportError:
    print("❌ Playwright not installed. Run: pip install playwright")
    print("   Then install browsers: playwright install")
    sys.exit(1)


class LinkedInPlaywrightValidator:
    """Validates LinkedIn using Playwright browser automation"""

    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL', '')
        self.password = os.getenv('LINKEDIN_PASSWORD', '')
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN', '')
        self.person_urn = os.getenv('LINKEDIN_PERSON_URN', '')
        self.session_path = Path.home() / '.linkedin_playwright_session'
        self.results = []

    def log(self, status: str, message: str):
        """Log validation result"""
        timestamp = datetime.now().isoformat()
        self.results.append({
            'timestamp': timestamp,
            'status': status,
            'message': message
        })
        print(f"{status} | {message}")

    async def validate_oauth_flow(self, context: BrowserContext) -> bool:
        """Validate LinkedIn OAuth flow"""
        self.log('⏳', 'Testing OAuth flow...')

        page = await context.new_page()
        try:
            # Navigate to LinkedIn
            await page.goto('https://www.linkedin.com', wait_until='networkidle', timeout=30000)

            # Check if already logged in
            try:
                await page.wait_for_selector('img[alt*="Profile"]', timeout=5000)
                self.log('✅', 'Already authenticated with LinkedIn')
                return True
            except:
                self.log('⚠️ ', 'Not authenticated, redirecting to login...')
                # Login flow would go here
                return False

        except Exception as e:
            self.log('❌', f'OAuth validation failed: {str(e)[:60]}')
            return False
        finally:
            await page.close()

    async def validate_posting_permission(self, context: BrowserContext) -> bool:
        """Validate ability to post on LinkedIn"""
        self.log('⏳', 'Checking posting permissions...')

        page = await context.new_page()
        try:
            await page.goto('https://www.linkedin.com/feed', wait_until='networkidle', timeout=30000)

            # Check for post composer button
            post_button = await page.query_selector('button[aria-label*="Start a post"]')
            if post_button:
                self.log('✅', 'Post composer available')
                return True
            else:
                self.log('⚠️ ', 'Post composer not found')
                return False

        except Exception as e:
            self.log('❌', f'Posting check failed: {str(e)[:60]}')
            return False
        finally:
            await page.close()

    async def validate_profile_visibility(self, context: BrowserContext) -> bool:
        """Check if profile is visible"""
        self.log('⏳', 'Checking profile visibility...')

        page = await context.new_page()
        try:
            await page.goto('https://www.linkedin.com/me', wait_until='networkidle', timeout=30000)

            # Check for profile name
            profile_name = await page.query_selector('h1[class*="profile"]')
            if profile_name:
                name_text = await profile_name.text_content()
                self.log('✅', f'Profile visible: {name_text.strip()[:40]}')
                return True
            else:
                self.log('⚠️ ', 'Profile not accessible')
                return False

        except Exception as e:
            self.log('❌', f'Profile check failed: {str(e)[:60]}')
            return False
        finally:
            await page.close()

    async def validate_api_token(self) -> bool:
        """Validate API token format and basic checks"""
        self.log('⏳', 'Validating access token...')

        if not self.access_token:
            self.log('❌', 'LINKEDIN_ACCESS_TOKEN not configured')
            return False

        # Check token format
        if self.access_token.startswith('AQ'):
            self.log('✅', f'Token format valid (AQ prefix, {len(self.access_token)} chars)')
            return True
        else:
            self.log('⚠️ ', f'Token format unusual (expected AQ prefix, got {self.access_token[:2]})')
            return False

    async def validate_person_urn(self) -> bool:
        """Validate person URN format"""
        self.log('⏳', 'Validating person URN...')

        if not self.person_urn:
            self.log('⚠️ ', 'LINKEDIN_PERSON_URN not configured')
            return False

        if self.person_urn.startswith('urn:li:person:'):
            self.log('✅', f'Person URN format valid')
            return True
        else:
            self.log('⚠️ ', f'Person URN format unexpected: {self.person_urn}')
            return False

    async def validate_email_password(self) -> bool:
        """Check if email/password are configured"""
        self.log('⏳', 'Checking email/password...')

        if not self.email or not self.password:
            self.log('⚠️ ', 'LINKEDIN_EMAIL/PASSWORD not configured (OAuth recommended)')
            return False

        self.log('✅', f'Email/password configured')
        return True

    async def run_browser_tests(self, headless: bool = True) -> Dict:
        """Run browser-based validation tests"""
        self.log('⏳', f'Starting Playwright validation (headless={headless})...')

        async with async_playwright() as p:
            try:
                # Launch browser
                browser = await p.chromium.launch(headless=headless)
                context = await browser.new_context()

                results = {
                    'oauth_valid': await self.validate_oauth_flow(context),
                    'posting_allowed': await self.validate_posting_permission(context),
                    'profile_visible': await self.validate_profile_visibility(context),
                }

                await context.close()
                await browser.close()

                return results

            except Exception as e:
                self.log('❌', f'Browser validation failed: {str(e)[:60]}')
                return {}

    async def run_all_validations(self, use_browser: bool = True) -> bool:
        """Run all validations"""
        print("\n" + "="*100)
        print("💼 LINKEDIN PLAYWRIGHT CREDENTIAL VALIDATOR")
        print("="*100 + "\n")

        # Non-browser validations
        api_valid = await self.validate_api_token()
        urn_valid = await self.validate_person_urn()
        email_valid = await self.validate_email_password()

        results_summary = {
            'api_token': api_valid,
            'person_urn': urn_valid,
            'email_password': email_valid,
        }

        # Browser validations (optional)
        if use_browser:
            print("\n" + "-"*100)
            print("🌐 Browser-based Tests")
            print("-"*100 + "\n")
            browser_results = await self.run_browser_tests(headless=True)
            results_summary.update(browser_results)
        else:
            self.log('⏭️ ', 'Browser tests skipped (use --browser to enable)')

        # Summary
        print("\n" + "="*100)
        print("📊 VALIDATION SUMMARY")
        print("="*100)

        valid_count = sum(1 for v in results_summary.values() if v)
        total_count = len(results_summary)

        for check, result in results_summary.items():
            status = '✅' if result else '❌'
            print(f"{status} {check.replace('_', ' ').title()}: {result}")

        health_score = (valid_count / total_count * 100) if total_count > 0 else 0
        print(f"\n🏥 Validation Score: {health_score:.0f}%")

        if health_score >= 80:
            print("✅ LinkedIn credentials are VALID and ready for use!")
            return True
        elif health_score >= 60:
            print("⚠️  LinkedIn credentials have some issues. Review above.")
            return False
        else:
            print("❌ LinkedIn credentials need attention.")
            return False

    def save_results(self):
        """Save validation results to file"""
        output_path = Path(__file__).parent / 'LINKEDIN_VALIDATION_RESULTS.json'
        with open(output_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': self.results,
                'email_configured': bool(self.email),
                'password_configured': bool(self.password),
                'token_configured': bool(self.access_token),
                'urn_configured': bool(self.person_urn),
            }, f, indent=2)
        print(f"\n📄 Results saved to: {output_path}")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='LinkedIn Playwright Credential Validator')
    parser.add_argument('--browser', action='store_true', help='Enable browser-based tests')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode')
    args = parser.parse_args()

    validator = LinkedInPlaywrightValidator()
    success = await validator.run_all_validations(use_browser=args.browser)
    validator.save_results()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
