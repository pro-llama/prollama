"""Tests for AST manipulation functionality."""

import ast
from unittest.mock import Mock, patch

import pytest

from prollama.anonymizer import ASTAnonymizer


class TestASTAnonymizer:
    """Test AST-based code anonymization."""

    def test_anonymize_string_literals(self):
        """Test that string literals are preserved but identifiers are anonymized."""
        code = '''
def hello():
    name = "John Doe"
    email = "john@example.com"
    return f"Hello, {name}!"
'''
        anonymizer = ASTAnonymizer()
        result, mappings = anonymizer.anonymize(code)
        
        # Should preserve string literals but anonymize function names
        assert "John Doe" in result  # String literals should be preserved
        assert "john@example.com" in result  # String literals should be preserved
        assert "def hello():" not in result  # Function name should be anonymized
        assert "def var_" in result  # Generic replacement should be used
        assert "return" in result  # Keywords should be preserved

    def test_anonymize_comments(self):
        """Test that comments are preserved but identifiers are anonymized."""
        code = '''
# API key: sk-1234567890abcdef
def get_data():
    # This is a safe comment
    return "data"
'''
        anonymizer = ASTAnonymizer()
        result, mappings = anonymizer.anonymize(code)
        
        # Should preserve comments but anonymize function names
        assert "sk-1234567890abcdef" in result  # Comments should be preserved
        assert "This is a safe comment" in result  # Comments should be preserved
        assert "def get_data():" not in result  # Function name should be anonymized
        assert "def var_" in result  # Generic replacement should be used

    def test_preserve_functionality(self):
        """Test that anonymized code remains functional with generic names."""
        code = '''
def calculate(x, y):
    # Calculate sum
    result = x + y
    return result

print(calculate(2, 3))
'''
        anonymizer = ASTAnonymizer()
        result, mappings = anonymizer.anonymize(code)
        
        # Code should still be valid Python but with anonymized function names
        try:
            compiled = compile(result, '<string>', 'exec')
            namespace = {}
            exec(compiled, namespace)
            # The function name will be anonymized, so we need to find it
            func_names = [name for name in namespace.keys() if name.startswith('var_')]
            assert len(func_names) == 1
            func = namespace[func_names[0]]
            assert func(2, 3) == 5
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
        result, mappings = anonymizer.anonymize(code)
        
        # Should preserve imports but anonymize function names
        assert "import os" in result
        assert "import sys" in result
        assert "from pathlib import Path" in result
        assert "def process():" not in result  # Function name should be anonymized
        assert "def var_" in result  # Generic replacement should be used

    def test_handle_multiline_strings(self):
        """Test proper handling of multiline strings while anonymizing identifiers."""
        code = '''
long_text = """
This is a multiline string
with email: user@example.com
and phone: 555-1234
"""
'''
        anonymizer = ASTAnonymizer()
        result, mappings = anonymizer.anonymize(code)
        
        # Should preserve multiline strings but anonymize variable names
        assert "user@example.com" in result  # String content should be preserved
        assert "555-1234" in result  # String content should be preserved
        assert '"""' in result or "'''" in result  # String delimiters should be preserved
        assert "long_text =" not in result  # Variable name should be anonymized
        assert "var_" in result  # Generic replacement should be used
