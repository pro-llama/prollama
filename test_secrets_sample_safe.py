#!/usr/bin/env python3
"""Sample Python file with SAFE test tokens for testing."""

import os
import requests
from prollama.testing.token_generators import (
    generate_test_aws_keys,
    generate_test_github_token,
    generate_test_openai_token,
    generate_test_database_url,
    token_generator
)

class ConfigManager:
    def __init__(self):
        # AWS Configuration (SAFE TEST TOKENS)
        self.aws_access_key, self.aws_secret_key = generate_test_aws_keys()
        
        # Database Configuration (SAFE)
        self.database_url = generate_test_database_url('postgresql')
        self.redis_url = generate_test_database_url('redis')
        
        # API Keys (SAFE TEST TOKENS)
        self.github_token = generate_test_github_token()
        self.slack_token = token_generator.generate_slack_token().token
        self.openai_token = generate_test_openai_token()
        self.anthropic_token = token_generator.generate_anthropic_token().token
        
        # Contact Information (SAFE)
        self.admin_email = token_generator.generate_email().token
        self.support_phone = "+1-555-TEST-1234"
        
        # SSH Key (SAFE TEST HEADER ONLY)
        self.ssh_private_key = f"""{token_generator.generate_ssh_key().token}
MIIEpAIBAAKCAQEA4f5wg5l2hKsTeNem/V41fGnJm6gOdrj8ym3rFkEjWT2btZb5
-----END TEST RSA PRIVATE KEY-----"""
        
        # JWT Token (SAFE)
        self.jwt_token = token_generator.generate_jwt_token().token
        
        # Payment (SAFE TEST)
        self.test_card = token_generator.generate_credit_card().token
    
    def get_headers(self):
        """Get API headers with authentication."""
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json",
            "User-Agent": "ConfigManager/1.0"
        }
    
    def connect_to_database(self):
        """Connect to the database."""
        import psycopg2
        return psycopg2.connect(self.database_url)
    
    def send_notification(self, message):
        """Send notification via Slack API."""
        payload = {
            "text": message,
            "channel": "#general"
        }
        
        headers = {
            "Authorization": f"Bearer {self.slack_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            json=payload,
            headers=headers
        )
        
        return response.json()
    
    def process_payment(self, amount, card_number):
        """Process payment with credit card."""
        # This is just for testing - never store real credit cards!
        payment_data = {
            "amount": amount,
            "card_number": card_number,
            "currency": "USD"
        }
        
        # In real implementation, this would use a payment processor
        return {"status": "success", "transaction_id": "txn_123456"}

def main():
    """Main function."""
    config = ConfigManager()
    
    print(f"Database URL: {config.database_url}")
    print(f"Admin email: {config.admin_email}")
    print(f"Support phone: {config.support_phone}")
    
    # Test API connection
    headers = config.get_headers()
    print(f"Using token: {config.github_token[:10]}...")
    
    # Test notification
    result = config.send_notification("Test message")
    print(f"Notification sent: {result}")
    
    # Print safety confirmation
    print("\n✅ All tokens are SAFE for GitHub upload:")
    print(f"   - AWS Access Key: {config.aws_access_key[:20]}...")
    print(f"   - GitHub Token: {config.github_token[:20]}...")
    print(f"   - OpenAI Token: {config.openai_token[:20]}...")
    print(f"   - Database URL: {config.database_url[:30]}...")

if __name__ == "__main__":
    main()
