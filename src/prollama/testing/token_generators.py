"""Secure token generators for testing purposes.

Generates realistic-looking but fake API tokens for various providers
that won't trigger real API access or be detected as actual secrets.
"""

import random
import string
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TokenInfo:
    """Information about a generated token."""
    provider: str
    token: str
    format_pattern: str
    is_safe: bool
    generation_time: datetime


class SecureTokenGenerator:
    """Generates safe test tokens for various cloud providers and services."""
    
    def __init__(self):
        """Initialize the token generator with safe prefixes."""
        # Safe prefixes that clearly indicate test tokens
        self.safe_prefixes = {
            'aws': ['TEST_AKIA', 'DEMO_AKIA', 'SAMPLE_AKIA'],
            'github': ['test_ghp_', 'demo_ghp_', 'sample_ghp_', 'fake_ghp_'],
            'github_app': ['test_ghs_', 'demo_ghs_', 'sample_ghs_', 'fake_ghs_'],
            'github_refresh': ['test_ghr_', 'demo_ghr_', 'sample_ghr_', 'fake_ghr_'],
            'openai': ['sk-test-', 'sk-demo-', 'sk-sample-', 'sk-fake-'],
            'anthropic': ['sk-test-ant-', 'sk-demo-ant-', 'sk-sample-ant-', 'sk-fake-ant-'],
            'slack': ['xoxb-test-', 'xoxb-demo-', 'xoxb-sample-', 'xoxb-fake-'],
            'stripe': ['sk_test_', 'sk_demo_', 'sk_sample_', 'sk_fake_'],
            'google': ['test_', 'demo_', 'sample_', 'fake_'],
            'azure': ['test_', 'demo_', 'sample_', 'fake_'],
            'twilio': ['ACtest', 'ACdemo', 'ACsample', 'ACfake'],
        }
        
        # Safe suffixes that indicate test tokens
        self.safe_suffixes = [
            'TEST_TOKEN', 'DEMO_KEY', 'SAMPLE_SECRET', 'FAKE_CREDENTIAL',
            'TESTING_ONLY', 'DEMO_PURPOSE', 'SAMPLE_DATA', 'FAKE_AUTH'
        ]
    
    def _random_string(self, length: int, charset: str = string.ascii_letters + string.digits) -> str:
        """Generate a random string of specified length."""
        return ''.join(random.choices(charset, k=length))
    
    def _random_base64(self, length: int) -> str:
        """Generate a random base64-like string."""
        chars = string.ascii_letters + string.digits + '+/'
        return self._random_string(length, chars)
    
    def _random_hex(self, length: int) -> str:
        """Generate a random hex string."""
        chars = '0123456789abcdef'
        return self._random_string(length, chars)
    
    def _is_safe_token(self, token: str) -> bool:
        """Validate that a token is safe (not a real credential)."""
        # Check for safe prefixes
        for provider, prefixes in self.safe_prefixes.items():
            if any(token.startswith(prefix) for prefix in prefixes):
                return True
        
        # Check for safe suffixes
        if any(suffix in token.upper() for suffix in self.safe_suffixes):
            return True
        
        # Check for obvious test patterns
        test_indicators = [
            'TEST', 'DEMO', 'SAMPLE', 'FAKE', 'MOCK', 'DUMMY',
            'EXAMPLE', 'PLACEHOLDER', 'XXXXX', 'YYYYY'
        ]
        
        return any(indicator in token.upper() for indicator in test_indicators)
    
    def generate_aws_access_key(self) -> TokenInfo:
        """Generate a safe AWS access key ID."""
        prefix = random.choice(self.safe_prefixes['aws'])
        # AWS keys are 20 chars: prefix (4-8) + 16 chars alphanumeric
        suffix = self._random_string(20 - len(prefix))
        token = prefix + suffix
        
        return TokenInfo(
            provider='AWS',
            token=token,
            format_pattern=f'{prefix}{{16_alphanumeric}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_aws_secret_key(self) -> TokenInfo:
        """Generate a safe AWS secret access key."""
        # AWS secret keys are 40 chars base64-like
        prefix = random.choice(['TEST_', 'DEMO_', 'SAMPLE_', 'FAKE_'])
        suffix = self._random_base64(40 - len(prefix))
        token = prefix + suffix
        
        return TokenInfo(
            provider='AWS',
            token=token,
            format_pattern=f'{prefix}{{40_base64_chars}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_github_token(self) -> TokenInfo:
        """Generate a safe GitHub personal access token."""
        prefix = random.choice(self.safe_prefixes['github'])
        # GitHub tokens are 40 chars after prefix
        suffix = self._random_string(40)
        token = prefix + suffix
        
        return TokenInfo(
            provider='GitHub',
            token=token,
            format_pattern=f'{prefix}{{40_alphanumeric}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_github_app_token(self) -> TokenInfo:
        """Generate a safe GitHub app token."""
        prefix = random.choice(self.safe_prefixes['github_app'])
        suffix = self._random_string(36)
        token = prefix + suffix
        
        return TokenInfo(
            provider='GitHub App',
            token=token,
            format_pattern=f'{prefix}{{36_alphanumeric}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_openai_token(self) -> TokenInfo:
        """Generate a safe OpenAI API key."""
        prefix = random.choice(self.safe_prefixes['openai'])
        # OpenAI keys are 48 chars total
        suffix = self._random_string(48 - len(prefix))
        token = prefix + suffix
        
        return TokenInfo(
            provider='OpenAI',
            token=token,
            format_pattern=f'{prefix}{{48_alphanumeric}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_anthropic_token(self) -> TokenInfo:
        """Generate a safe Anthropic API key."""
        prefix = random.choice(self.safe_prefixes['anthropic'])
        # Anthropic keys are longer, around 50 chars
        suffix = self._random_string(50 - len(prefix))
        token = prefix + suffix
        
        return TokenInfo(
            provider='Anthropic',
            token=token,
            format_pattern=f'{prefix}{{50_alphanumeric}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_slack_token(self) -> TokenInfo:
        """Generate a safe Slack bot token."""
        prefix = random.choice(self.safe_prefixes['slack'])
        # Slack tokens are variable length, typically 50+ chars
        suffix = self._random_string(random.randint(30, 50))
        token = prefix + suffix
        
        return TokenInfo(
            provider='Slack',
            token=token,
            format_pattern=f'{prefix}{{30-50_alphanumeric}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_stripe_token(self) -> TokenInfo:
        """Generate a safe Stripe API key."""
        prefix = random.choice(self.safe_prefixes['stripe'])
        # Stripe test keys start with sk_test_
        suffix = self._random_string(40)
        token = prefix + suffix
        
        return TokenInfo(
            provider='Stripe',
            token=token,
            format_pattern=f'{prefix}{{40_alphanumeric}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_google_token(self) -> TokenInfo:
        """Generate a safe Google API token."""
        prefix = random.choice(self.safe_prefixes['google'])
        # Google service account keys are JSON, but access tokens are base64
        suffix = self._random_base64(80)
        token = prefix + suffix
        
        return TokenInfo(
            provider='Google',
            token=token,
            format_pattern=f'{prefix}{{80_base64_chars}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_azure_token(self) -> TokenInfo:
        """Generate a safe Azure API token."""
        prefix = random.choice(self.safe_prefixes['azure'])
        # Azure tokens are JWT-like
        header = self._random_base64(32)
        payload = self._random_base64(48)
        signature = self._random_base64(43)
        token = prefix + f"{header}.{payload}.{signature}"
        
        return TokenInfo(
            provider='Azure',
            token=token,
            format_pattern=f'{prefix}{{base64_header.payload.signature}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_twilio_token(self) -> TokenInfo:
        """Generate a safe Twilio API token."""
        prefix = random.choice(self.safe_prefixes['twilio'])
        # Twilio account SID is 34 chars starting with AC
        suffix = self._random_string(34 - len(prefix))
        token = prefix + suffix
        
        return TokenInfo(
            provider='Twilio',
            token=token,
            format_pattern=f'{prefix}{{34_alphanumeric}}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_jwt_token(self, payload: Optional[Dict] = None) -> TokenInfo:
        """Generate a safe JWT token."""
        if payload is None:
            payload = {
                "iss": "test-issuer",
                "sub": "test-user",
                "aud": "test-audience",
                "exp": 1234567890,
                "iat": 1234567800,
                "purpose": "TESTING_ONLY"
            }
        
        # Create fake JWT parts
        import json
        import base64
        
        # Header
        header = {"alg": "HS256", "typ": "JWT", "kid": "TEST_KEY"}
        header_b64 = base64.b64encode(json.dumps(header).encode()).decode().rstrip('=')
        
        # Payload
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        
        # Signature (fake)
        signature = self._random_base64(43)
        
        token = f"{header_b64}.{payload_b64}.{signature}"
        
        return TokenInfo(
            provider='JWT',
            token=token,
            format_pattern='base64_header.base64_payload.base64_signature',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_database_url(self, provider: str = 'postgresql') -> TokenInfo:
        """Generate a safe database URL."""
        safe_username = f"test_user_{random.randint(100, 999)}"
        safe_password = f"test_pass_{random.randint(100, 999)}"
        safe_host = f"test-{provider}.example.com"
        safe_db = f"test_db_{random.randint(100, 999)}"
        
        token = f"{provider}://{safe_username}:{safe_password}@{safe_host}:5432/{safe_db}"
        
        return TokenInfo(
            provider=f'{provider.upper()} Database',
            token=token,
            format_pattern=f'{provider}://test_user:test_pass@test-host:5432/test_db',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_ssh_key(self) -> TokenInfo:
        """Generate a safe SSH private key header."""
        # Only generate the header, not the full key
        key_types = ['RSA', 'DSA', 'EC', 'OPENSSH']
        key_type = random.choice(key_types)
        
        # Add test indicator
        token = f"-----BEGIN TEST {key_type} PRIVATE KEY-----"
        
        return TokenInfo(
            provider='SSH',
            token=token,
            format_pattern='-----BEGIN TEST {KEY_TYPE} PRIVATE KEY-----',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_email(self) -> TokenInfo:
        """Generate a safe email address."""
        domains = ['test.com', 'example.org', 'demo.net', 'sample.io']
        usernames = ['test.user', 'demo.account', 'sample.email', 'fake.contact']
        
        username = random.choice(usernames) + str(random.randint(100, 999))
        domain = random.choice(domains)
        
        token = f"{username}@{domain}"
        
        return TokenInfo(
            provider='Email',
            token=token,
            format_pattern='test.user{number}@{test_domain}',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_credit_card(self) -> TokenInfo:
        """Generate a safe credit card number."""
        # Use test credit card numbers that are clearly fake
        test_prefixes = ['4111', '4000', '5555', '5105']  # Known test prefixes
        
        prefix = random.choice(test_prefixes)
        # Generate remaining digits to make 16 digits total
        remaining = self._random_string(16 - len(prefix), string.digits)
        
        # Add test indicator in the middle
        token = prefix + 'TEST' + remaining[4:]
        
        return TokenInfo(
            provider='Credit Card',
            token=token,
            format_pattern='TEST_CARD_NUMBER',
            is_safe=self._is_safe_token(token),
            generation_time=datetime.now()
        )
    
    def generate_all_tokens(self) -> List[TokenInfo]:
        """Generate one of each supported token type."""
        tokens = [
            self.generate_aws_access_key(),
            self.generate_aws_secret_key(),
            self.generate_github_token(),
            self.generate_github_app_token(),
            self.generate_openai_token(),
            self.generate_anthropic_token(),
            self.generate_slack_token(),
            self.generate_stripe_token(),
            self.generate_google_token(),
            self.generate_azure_token(),
            self.generate_twilio_token(),
            self.generate_jwt_token(),
            self.generate_database_url('postgresql'),
            self.generate_database_url('mysql'),
            self.generate_database_url('mongodb'),
            self.generate_ssh_key(),
            self.generate_email(),
            self.generate_credit_card(),
        ]
        
        return tokens
    
    def generate_token_by_type(self, token_type: str) -> TokenInfo:
        """Generate a token of a specific type."""
        generators = {
            'aws_access': self.generate_aws_access_key,
            'aws_secret': self.generate_aws_secret_key,
            'github': self.generate_github_token,
            'github_app': self.generate_github_app_token,
            'openai': self.generate_openai_token,
            'anthropic': self.generate_anthropic_token,
            'slack': self.generate_slack_token,
            'stripe': self.generate_stripe_token,
            'google': self.generate_google_token,
            'azure': self.generate_azure_token,
            'twilio': self.generate_twilio_token,
            'jwt': self.generate_jwt_token,
            'database_postgresql': lambda: self.generate_database_url('postgresql'),
            'database_mysql': lambda: self.generate_database_url('mysql'),
            'database_mongodb': lambda: self.generate_database_url('mongodb'),
            'ssh': self.generate_ssh_key,
            'email': self.generate_email,
            'credit_card': self.generate_credit_card,
        }
        
        if token_type not in generators:
            raise ValueError(f"Unknown token type: {token_type}. Available: {list(generators.keys())}")
        
        return generators[token_type]()
    
    def validate_token_safety(self, token: str) -> Dict[str, any]:
        """Validate that a token is safe for testing."""
        return {
            'token': token,
            'is_safe': self._is_safe_token(token),
            'length': len(token),
            'has_safe_prefix': any(token.startswith(prefix) for prefixes in self.safe_prefixes.values() for prefix in prefixes),
            'has_safe_suffix': any(suffix in token.upper() for suffix in self.safe_suffixes),
            'has_test_indicators': any(indicator in token.upper() for indicator in ['TEST', 'DEMO', 'SAMPLE', 'FAKE']),
        }


# Global instance for easy access
token_generator = SecureTokenGenerator()


# Convenience functions
def generate_test_aws_keys() -> tuple[str, str]:
    """Generate test AWS access key and secret key."""
    access_key = token_generator.generate_aws_access_key()
    secret_key = token_generator.generate_aws_secret_key()
    return access_key.token, secret_key.token


def generate_test_github_token() -> str:
    """Generate a test GitHub token."""
    return token_generator.generate_github_token().token


def generate_test_openai_token() -> str:
    """Generate a test OpenAI token."""
    return token_generator.generate_openai_token().token


def generate_test_database_url(provider: str = 'postgresql') -> str:
    """Generate a test database URL."""
    return token_generator.generate_database_url(provider).token


def generate_all_test_tokens() -> Dict[str, str]:
    """Generate all test tokens and return as a dictionary."""
    tokens = token_generator.generate_all_tokens()
    return {token.provider: token.token for token in tokens}
