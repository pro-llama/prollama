"""Tests for AST manipulation functionality."""

import ast
from unittest.mock import Mock, patch

import pytest

from prollama.anonymizer import ASTAnonymizer


class TestASTAnonymizer:
    """Test AST-based code anonymization."""

    def test_anonymize_string_literals(self):
        """Test that string literals are properly anonymized."""
        code = '''
def hello():
    name = "John Doe"
    email = "john@example.com"
    return f"Hello, {name}!"
'''
        anonymizer = ASTAnonymizer()
        result = anonymizer.anonymize(code)
        
        # Should replace personal data but preserve structure
        assert "John Doe" not in result
        assert "john@example.com" not in result
        assert "def hello():" in result
        assert "return" in result

    def test_anonymize_comments(self):
        """Test that comments containing sensitive data are removed."""
        code = '''
# API key: sk-1234567890abcdef
def get_data():
    # This is a safe comment
    return "data"
'''
        anonymizer = ASTAnonymizer()
        result = anonymizer.anonymize(code)
        
        assert "sk-1234567890abcdef" not in result
        assert "This is a safe comment" in result
        assert "def get_data():" in result

    def test_preserve_functionality(self):
        """Test that anonymized code remains functional."""
        code = '''
def calculate(x, y):
    # Calculate sum
    result = x + y
    return result

print(calculate(2, 3))
'''
        anonymizer = ASTAnonymizer()
        result = anonymizer.anonymize(code)
        
        # Code should still be valid Python
        try:
            compiled = compile(result, '<string>', 'exec')
            namespace = {}
            exec(compiled, namespace)
            assert namespace['calculate'](2, 3) == 5
        except SyntaxError:
            pytest.fail("Anonymized code has invalid syntax")

    def test_detect_secrets(self):
        """Test detection of potential secrets in code."""
        code = '''
API_KEY = "sk-1234567890abcdef"
PASSWORD = "secret123"
TOKEN = "ghp_1234567890abcdef"
'''
        anonymizer = ASTAnonymizer()
        secrets = anonymizer.detect_secrets(code)
        
        assert len(secrets) >= 3
        assert any('sk-' in secret for secret in secrets)
        assert any('secret' in secret.lower() for secret in secrets)
        assert any('ghp_' in secret for secret in secrets)

    def test_preserve_imports(self):
        """Test that imports are preserved during anonymization."""
        code = '''
import os
import sys
from pathlib import Path

def process():
    return os.getcwd()
'''
        anonymizer = ASTAnonymizer()
        result = anonymizer.anonymize(code)
        
        assert "import os" in result
        assert "import sys" in result
        assert "from pathlib import Path" in result
        assert "def process():" in result

    def test_handle_multiline_strings(self):
        """Test proper handling of multiline strings."""
        code = '''
long_text = """
This is a multiline string
with email: user@example.com
and phone: 555-1234
"""
'''
        anonymizer = ASTAnonymizer()
        result = anonymizer.anonymize(code)
        
        assert "user@example.com" not in result
        assert "555-1234" not in result
        assert '"""' in result or "'''" in result
