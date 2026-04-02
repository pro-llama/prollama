# Secure Token Generators for Testing

## Overview

This module provides secure token generators for testing purposes that create realistic-looking but fake API tokens. These tokens are designed to be detected by content filtering systems while being clearly marked as test credentials to prevent accidental use in production.

## Features

### 🔒 Safe Token Generation
- **17 different provider types** supported
- **Built-in safety validation** to ensure tokens aren't real credentials
- **Clear test indicators** (TEST/DEMO/SAMPLE/FAKE prefixes)
- **Realistic format patterns** that match actual provider formats

### 🛡️ Security Features
- **Automatic safety validation** - tokens are checked against known patterns
- **Test-only indicators** - clearly marked as fake/for testing
- **No real API access** - tokens won't work with actual services
- **GitHub-safe** - won't trigger real credential alerts when uploaded

### 📊 Supported Providers

| Provider | Token Type | Example Prefix | Length |
|----------|------------|----------------|--------|
| AWS | Access Key | `TEST_AKIA` | 20 chars |
| AWS | Secret Key | `FAKE_` | 40 chars |
| GitHub | Personal Token | `test_ghp_` | 40 chars |
| GitHub | App Token | `demo_ghs_` | 36 chars |
| OpenAI | API Key | `sk-sample-` | 48 chars |
| Anthropic | API Key | `sk-demo-ant-` | 50 chars |
| Slack | Bot Token | `xoxb-test-` | 30-50 chars |
| Stripe | API Key | `sk_sample_` | 40 chars |
| Google | Service Token | `demo_` | 80+ chars |
| Azure | JWT Token | `test_` | Variable |
| Twilio | Account SID | `ACtest` | 34 chars |
| Database | PostgreSQL URL | `test_user_` | Variable |
| SSH | Private Key | `-----BEGIN TEST` | Header only |
| Email | Address | `test.user` | Variable |
| Credit Card | Number | `TEST_CARD` | 16 chars |

## Usage

### Basic Usage

```python
from prollama.testing.token_generators import (
    generate_test_aws_keys,
    generate_test_github_token,
    generate_test_openai_token,
    token_generator
)

# Generate individual tokens
access_key, secret_key = generate_test_aws_keys()
github_token = generate_test_github_token()
openai_token = generate_test_openai_token()

print(f"AWS Access Key: {access_key}")
print(f"GitHub Token: {github_token}")
```

### Advanced Usage

```python
from prollama.testing.token_generators import SecureTokenGenerator

generator = SecureTokenGenerator()

# Generate specific token types
aws_token = generator.generate_aws_access_key()
slack_token = generator.generate_slack_token()
jwt_token = generator.generate_jwt_token()

# Generate all token types
all_tokens = generator.generate_all_tokens()

# Validate token safety
validation = generator.validate_token_safety(aws_token.token)
print(f"Is safe: {validation['is_safe']}")
```

### Integration with Tests

```python
# In your test files
from prollama.testing.token_generators import generate_all_test_tokens

def test_api_integration():
    tokens = generate_all_test_tokens()
    
    # Use tokens in your test
    config = {
        'aws_access_key': tokens['AWS'],
        'github_token': tokens['GitHub'],
        'database_url': tokens['POSTGRESQL Database']
    }
    
    # Test your code with these safe tokens
    result = your_api_function(config)
    assert result.success
```

## Safety Features

### Automatic Safety Checks

Every generated token is validated to ensure it's safe:

```python
validation = generator.validate_token_safety(token)
# Returns:
# {
#     'token': 'DEMO_AKIAk3N6Dole9CK',
#     'is_safe': True,
#     'length': 20,
#     'has_safe_prefix': True,
#     'has_safe_suffix': False,
#     'has_test_indicators': True
# }
```

### Safety Criteria

Tokens are considered safe if they have:
- ✅ Safe prefixes (TEST/DEMO/SAMPLE/FAKE)
- ✅ Test indicators in the token
- ✅ Clearly fake patterns
- ❌ No real provider patterns

## Integration with Content Filter

The generated tokens work perfectly with the content filtering system:

```python
from prollama.security.content_filter import ContentFilter
from prollama.testing.token_generators import generate_test_github_token

filter = ContentFilter()
token = generate_test_github_token()

# Token will be detected but marked as safe
content = f"GITHUB_TOKEN = '{token}'"
detections = filter.filter_content(content)

print(f"Detections: {len(detections)}")  # Will detect the token
print(f"Safe for GitHub: {token.startswith('test_')}")  # True
```

## Examples

### Test Configuration File

```python
#!/usr/bin/env python3
"""Safe test configuration using generated tokens."""

from prollama.testing.token_generators import generate_all_test_tokens

class TestConfig:
    def __init__(self):
        tokens = generate_all_test_tokens()
        
        # Safe AWS configuration
        self.aws_access_key = tokens['AWS']
        self.aws_secret_key = tokens['AWS']  # Different secret key
        
        # Safe API tokens
        self.github_token = tokens['GitHub']
        self.openai_token = tokens['OpenAI']
        self.slack_token = tokens['Slack']
        
        # Safe database URLs
        self.postgres_url = tokens['POSTGRESQL Database']
        self.mongodb_url = tokens['MONGODB Database']
        
        # Safe contact info
        self.admin_email = tokens['Email']
        self.test_card = tokens['Credit Card']
```

### CLI Integration

```bash
# Test with safe tokens
prollama anonymize test_file.py --filter-secrets

# The content filter will detect the generated tokens
# but they're clearly marked as safe for GitHub upload
```

## Migration Guide

### From Static Tokens

**Before (unsafe - DO NOT USE):**
```python
# These examples are for illustration only - DO NOT COMMIT!
# AWS_ACCESS_KEY_ID = "REDACTED_AWS_KEY"  # Real-looking!
# GITHUB_TOKEN = "REDACTED_GITHUB_TOKEN"  # Dangerous!
```

**After (safe):**
```python
from prollama.testing.token_generators import generate_test_aws_keys, generate_test_github_token

AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY = generate_test_aws_keys()
GITHUB_TOKEN = generate_test_github_token()
# Results: Safe tokens with TEST/DEMO prefixes
# Note: The results shown are examples - actual tokens will be different each time
```

## Best Practices

### ✅ Do
- Use generated tokens in all test files
- Validate tokens before using them
- Include test indicators in token names
- Use different tokens for different test scenarios
- Document that tokens are for testing only

### ❌ Don't
- Use real-looking tokens without test indicators
- Commit static tokens that look real
- Use generated tokens in production code
- Share tokens that might be mistaken for real ones
- Remove the test indicators from generated tokens

## Testing

Run the comprehensive test suite:

```bash
python test_secure_tokens.py
```

This will test:
- ✅ All token generators
- ✅ Safety validation
- ✅ Content filter integration
- ✅ Convenience functions
- ✅ Token format compliance

## Security Considerations

These tokens are designed to be:
- **Detectable** by security scanners (as they should be)
- **Safe** for GitHub upload and sharing
- **Non-functional** with real APIs
- **Clearly marked** as test credentials

However, always:
- Review generated tokens before committing
- Ensure test environments are isolated
- Use environment-specific configurations
- Follow your organization's security policies

## Contributing

To add a new token generator:

1. Add the provider to `safe_prefixes`
2. Implement the generator method
3. Add it to `generate_all_tokens()`
4. Add tests in `test_secure_tokens.py`
5. Update this documentation

## License

This module is part of the prollama project and follows the same licensing terms.
