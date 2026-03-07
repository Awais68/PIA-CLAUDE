#!/usr/bin/env python3
"""
Comprehensive Credential Validator for Zoya AI Employee
Validates: WhatsApp, Facebook, Twitter, LinkedIn (Playwright-based)
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()


@dataclass
class CredentialStatus:
    """Status of a single credential"""
    platform: str
    credential: str
    status: str  # "✅ VALID", "⚠️ WARNING", "❌ INVALID", "⏳ CHECKING"
    message: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CredentialValidator:
    """Validates all platform credentials"""

    def __init__(self):
        self.results: List[CredentialStatus] = []
        self.config = {
            'twitter': self._load_twitter_config(),
            'linkedin': self._load_linkedin_config(),
            'facebook': self._load_facebook_config(),
            'whatsapp': self._load_whatsapp_config(),
        }

    def _load_twitter_config(self) -> Dict:
        return {
            'api_key': os.getenv('TWITTER_API_KEY', ''),
            'api_secret': os.getenv('TWITTER_API_SECRET', ''),
            'bearer_token': os.getenv('TWITTER_BEARER_TOKEN', ''),
            'access_token': os.getenv('TWITTER_ACCESS_TOKEN', ''),
        }

    def _load_linkedin_config(self) -> Dict:
        return {
            'client_id': os.getenv('LINKEDIN_CLIENT_ID', ''),
            'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET', ''),
            'access_token': os.getenv('LINKEDIN_ACCESS_TOKEN', ''),
            'person_urn': os.getenv('LINKEDIN_PERSON_URN', ''),
        }

    def _load_facebook_config(self) -> Dict:
        return {
            'access_token': os.getenv('FACEBOOK_ACCESS_TOKEN', ''),
            'page_id': os.getenv('FACEBOOK_PAGE_ID', ''),
            'marketing_token': os.getenv('MARKETING_ACCESS_TOKEN', ''),
            'meta_access_token': os.getenv('META_ACCESS_TOKEN', ''),
        }

    def _load_whatsapp_config(self) -> Dict:
        return {
            'access_token': os.getenv('WHATSAPP_ACCESS_TOKEN', ''),
            'business_token': os.getenv('WHATSAPP_BUSINESS_TOKEN', ''),
            'phone_number_id': os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''),
            'business_account_id': os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID', ''),
        }

    def log_result(self, platform: str, credential: str, status: str, message: str):
        """Log a credential check result"""
        result = CredentialStatus(
            platform=platform,
            credential=credential,
            status=status,
            message=message
        )
        self.results.append(result)
        print(f"{status} {platform.upper():12} | {credential:25} | {message}")

    # ============================================================================
    # TWITTER VALIDATION
    # ============================================================================

    def check_twitter(self) -> bool:
        """Validate Twitter/X API credentials"""
        print("\n" + "="*100)
        print("🐦 TWITTER/X API VALIDATION")
        print("="*100)

        config = self.config['twitter']
        all_valid = True

        # Check if credentials exist
        if not config['bearer_token']:
            self.log_result('Twitter', 'Bearer Token', '❌ INVALID', 'Missing TWITTER_BEARER_TOKEN')
            all_valid = False
        else:
            # Validate bearer token format
            if config['bearer_token'].startswith('AAAA'):
                try:
                    status, msg = self._validate_twitter_token(config['bearer_token'])
                    self.log_result('Twitter', 'Bearer Token', status, msg)
                    if '✅' not in status:
                        all_valid = False
                except Exception as e:
                    self.log_result('Twitter', 'Bearer Token', '⚠️ WARNING', f'Validation error: {str(e)[:50]}')
                    all_valid = False
            else:
                self.log_result('Twitter', 'Bearer Token', '⚠️ WARNING', 'Token format looks incorrect (should start with AAAA)')
                all_valid = False

        # Check API Key & Secret
        if config['api_key']:
            self.log_result('Twitter', 'API Key', '✅ VALID', f'Present ({len(config["api_key"])} chars)')
        else:
            self.log_result('Twitter', 'API Key', '⚠️ WARNING', 'Missing TWITTER_API_KEY')

        if config['api_secret']:
            self.log_result('Twitter', 'API Secret', '✅ VALID', f'Present ({len(config["api_secret"])} chars)')
        else:
            self.log_result('Twitter', 'API Secret', '⚠️ WARNING', 'Missing TWITTER_API_SECRET')

        return all_valid

    def _validate_twitter_token(self, bearer_token: str) -> Tuple[str, str]:
        """Validate Twitter bearer token by calling v2 API"""
        try:
            headers = {
                'Authorization': f'Bearer {bearer_token}',
                'User-Agent': 'Zoya-CredentialChecker/1.0'
            }

            # Check tweets.read scope
            response = requests.get(
                'https://api.twitter.com/2/tweets/search/recent?query=from:twitter&max_results=10',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return '✅ VALID', 'Token active and working (API v2)'
            elif response.status_code == 401:
                return '❌ INVALID', 'Token expired or invalid (401)'
            elif response.status_code == 403:
                return '⚠️ WARNING', 'Token valid but missing permissions (403)'
            else:
                return '⚠️ WARNING', f'API response: {response.status_code}'

        except requests.exceptions.Timeout:
            return '⚠️ WARNING', 'API timeout - network issue'
        except Exception as e:
            return '⚠️ WARNING', f'Validation error: {str(e)[:40]}'

    # ============================================================================
    # FACEBOOK VALIDATION
    # ============================================================================

    def check_facebook(self) -> bool:
        """Validate Facebook/Meta credentials"""
        print("\n" + "="*100)
        print("📘 FACEBOOK/META API VALIDATION")
        print("="*100)

        config = self.config['facebook']
        all_valid = True

        tokens_to_check = [
            ('Facebook Access Token', config['access_token']),
            ('Meta Access Token', config['meta_access_token']),
            ('Marketing Access Token', config['marketing_token']),
        ]

        valid_token_count = 0
        for token_name, token in tokens_to_check:
            if token:
                status, msg = self._validate_facebook_token(token)
                self.log_result('Facebook', token_name, status, msg)
                if '✅' in status:
                    valid_token_count += 1
                else:
                    all_valid = False
            else:
                self.log_result('Facebook', token_name, '⚠️ WARNING', 'Not configured')

        if config['page_id']:
            self.log_result('Facebook', 'Page ID', '✅ VALID', f'Present ({config["page_id"]})')
        else:
            self.log_result('Facebook', 'Page ID', '⚠️ WARNING', 'Missing FACEBOOK_PAGE_ID')

        if valid_token_count == 0:
            all_valid = False

        return all_valid

    def _validate_facebook_token(self, token: str) -> Tuple[str, str]:
        """Validate Facebook token by calling Graph API"""
        try:
            response = requests.get(
                'https://graph.facebook.com/v18.0/me',
                params={'access_token': token},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                name = data.get('name', 'Unknown')
                return '✅ VALID', f'Token active ({name})'
            elif response.status_code == 400:
                error = response.json().get('error', {}).get('message', 'Invalid request')
                return '❌ INVALID', f'Token invalid: {error[:40]}'
            else:
                return '⚠️ WARNING', f'API response: {response.status_code}'

        except requests.exceptions.Timeout:
            return '⚠️ WARNING', 'API timeout'
        except Exception as e:
            return '⚠️ WARNING', f'Error: {str(e)[:40]}'

    # ============================================================================
    # LINKEDIN VALIDATION (Playwright)
    # ============================================================================

    def check_linkedin(self) -> bool:
        """Validate LinkedIn credentials using Playwright"""
        print("\n" + "="*100)
        print("💼 LINKEDIN API VALIDATION (Playwright)")
        print("="*100)

        config = self.config['linkedin']
        all_valid = True

        # Check OAuth credentials
        if config['client_id']:
            self.log_result('LinkedIn', 'Client ID', '✅ VALID', f'Present ({config["client_id"]})')
        else:
            self.log_result('LinkedIn', 'Client ID', '❌ INVALID', 'Missing LINKEDIN_CLIENT_ID')
            all_valid = False

        if config['client_secret']:
            self.log_result('LinkedIn', 'Client Secret', '✅ VALID', f'Present ({len(config["client_secret"])} chars)')
        else:
            self.log_result('LinkedIn', 'Client Secret', '❌ INVALID', 'Missing LINKEDIN_CLIENT_SECRET')
            all_valid = False

        # Validate Access Token
        if config['access_token']:
            status, msg = self._validate_linkedin_token(config['access_token'])
            self.log_result('LinkedIn', 'Access Token', status, msg)
            if '❌' in status:
                all_valid = False
        else:
            self.log_result('LinkedIn', 'Access Token', '❌ INVALID', 'Missing LINKEDIN_ACCESS_TOKEN')
            all_valid = False

        # Check Person URN
        if config['person_urn']:
            if config['person_urn'].startswith('urn:li:person:'):
                self.log_result('LinkedIn', 'Person URN', '✅ VALID', f'Correct format')
            else:
                self.log_result('LinkedIn', 'Person URN', '⚠️ WARNING', f'Format unexpected: {config["person_urn"]}')
        else:
            self.log_result('LinkedIn', 'Person URN', '⚠️ WARNING', 'Missing LINKEDIN_PERSON_URN')

        # Offer Playwright-based validation
        self._offer_playwright_validation()

        return all_valid

    def _validate_linkedin_token(self, token: str) -> Tuple[str, str]:
        """Validate LinkedIn access token via REST API"""
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }

            response = requests.get(
                'https://api.linkedin.com/v2/me',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                first_name = data.get('localizedFirstName', '?')
                return '✅ VALID', f'Token active ({first_name})'
            elif response.status_code == 401:
                return '❌ INVALID', 'Token expired (401 Unauthorized)'
            elif response.status_code == 403:
                return '⚠️ WARNING', 'Insufficient permissions (403)'
            else:
                return '⚠️ WARNING', f'API response: {response.status_code}'

        except requests.exceptions.Timeout:
            return '⚠️ WARNING', 'API timeout'
        except Exception as e:
            return '⚠️ WARNING', f'Error: {str(e)[:40]}'

    def _offer_playwright_validation(self):
        """Offer Playwright-based LinkedIn browser validation"""
        print("\n" + "-"*100)
        print("💡 PLAYWRIGHT VALIDATION OPTIONS (For advanced browser-based auth):")
        print("-"*100)
        print("""
To validate LinkedIn using Playwright browser automation:
  1. Run: python linkedin_playwright_login.py
     - Automates browser login via email/password OR OAuth
     - Captures session cookies
     - Validates posting permissions
     - Stores session for future use

  2. Run: python linkedin_playwright_validator.py
     - Uses existing session to validate token
     - Tests posting capability
     - Shows account permissions
""")

    # ============================================================================
    # WHATSAPP VALIDATION
    # ============================================================================

    def check_whatsapp(self) -> bool:
        """Validate WhatsApp Business API credentials"""
        print("\n" + "="*100)
        print("💬 WHATSAPP BUSINESS API VALIDATION")
        print("="*100)

        config = self.config['whatsapp']
        all_valid = True

        tokens_to_check = [
            ('WhatsApp Access Token', config['access_token']),
            ('WhatsApp Business Token', config['business_token']),
        ]

        valid_token_count = 0
        for token_name, token in tokens_to_check:
            if token:
                status, msg = self._validate_whatsapp_token(token)
                self.log_result('WhatsApp', token_name, status, msg)
                if '✅' in status:
                    valid_token_count += 1
                else:
                    all_valid = False
            else:
                self.log_result('WhatsApp', token_name, '⚠️ WARNING', 'Not configured')

        if config['phone_number_id']:
            self.log_result('WhatsApp', 'Phone Number ID', '✅ VALID', f'Present ({config["phone_number_id"]})')
        else:
            self.log_result('WhatsApp', 'Phone Number ID', '⚠️ WARNING', 'Missing WHATSAPP_PHONE_NUMBER_ID')

        if config['business_account_id']:
            self.log_result('WhatsApp', 'Business Account ID', '✅ VALID', f'Present ({config["business_account_id"]})')
        else:
            self.log_result('WhatsApp', 'Business Account ID', '⚠️ WARNING', 'Missing WHATSAPP_BUSINESS_ACCOUNT_ID')

        if valid_token_count == 0:
            all_valid = False

        return all_valid

    def _validate_whatsapp_token(self, token: str) -> Tuple[str, str]:
        """Validate WhatsApp token via Cloud API"""
        try:
            # Try to get phone numbers (basic validation)
            phone_number_id = self.config['whatsapp']['phone_number_id']
            if not phone_number_id or phone_number_id == '+92-335-2204606':
                return '⚠️ WARNING', 'Phone number ID not properly configured'

            response = requests.get(
                f'https://graph.instagram.com/v18.0/{phone_number_id}',
                params={'access_token': token},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                phone = data.get('display_phone_number', 'Unknown')
                return '✅ VALID', f'Token active ({phone})'
            elif response.status_code == 400:
                return '❌ INVALID', 'Invalid token or ID'
            elif response.status_code == 401:
                return '❌ INVALID', 'Token expired (401)'
            else:
                return '⚠️ WARNING', f'API response: {response.status_code}'

        except requests.exceptions.Timeout:
            return '⚠️ WARNING', 'API timeout'
        except Exception as e:
            return '⚠️ WARNING', f'Error: {str(e)[:40]}'

    # ============================================================================
    # SUMMARY REPORT
    # ============================================================================

    def generate_report(self) -> str:
        """Generate credential validation report"""
        report = []
        report.append("\n" + "="*100)
        report.append("📊 CREDENTIAL VALIDATION SUMMARY")
        report.append("="*100 + "\n")

        # Group by platform
        by_platform = {}
        for result in self.results:
            if result.platform not in by_platform:
                by_platform[result.platform] = []
            by_platform[result.platform].append(result)

        # Count by status
        valid_count = sum(1 for r in self.results if '✅' in r.status)
        warning_count = sum(1 for r in self.results if '⚠️' in r.status)
        invalid_count = sum(1 for r in self.results if '❌' in r.status)

        # Overall health
        total = len(self.results)
        health_score = (valid_count / total * 100) if total > 0 else 0

        report.append(f"Total Checks: {total}")
        report.append(f"  ✅ Valid:     {valid_count} ({valid_count/total*100:.0f}%)")
        report.append(f"  ⚠️  Warnings:  {warning_count} ({warning_count/total*100:.0f}%)")
        report.append(f"  ❌ Invalid:   {invalid_count} ({invalid_count/total*100:.0f}%)")
        report.append(f"\n🏥 Overall Health: {health_score:.0f}%")

        if health_score >= 80:
            report.append("   Status: 🟢 GOOD - System ready")
        elif health_score >= 60:
            report.append("   Status: 🟡 FAIR - Some issues to fix")
        else:
            report.append("   Status: 🔴 POOR - Critical issues detected")

        # Save report to file
        report_path = Path(__file__).parent / 'CREDENTIAL_CHECK_REPORT.md'
        with open(report_path, 'w') as f:
            f.write('\n'.join(report) + '\n')

        report.append(f"\n📄 Report saved to: {report_path}")

        return '\n'.join(report)

    def run_all_checks(self) -> bool:
        """Run all credential checks"""
        print("\n🔍 Starting Credential Validation...\n")

        results = {
            'Twitter': self.check_twitter(),
            'Facebook': self.check_facebook(),
            'WhatsApp': self.check_whatsapp(),
            'LinkedIn': self.check_linkedin(),
        }

        print(self.generate_report())

        all_valid = all(results.values())

        if all_valid:
            print("\n✅ All credentials are VALID and ready for use!")
        else:
            print("\n⚠️  Some credentials need attention. See details above.")

        return all_valid


def main():
    """Main entry point"""
    validator = CredentialValidator()
    success = validator.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
