#!/usr/bin/env python3
"""Comparison tests with other secret scanning tools using SAFE tokens."""

import time
import re
from pathlib import Path
from prollama.security.content_filter import ContentFilter
from prollama.testing.token_generators import token_generator


def simulate_trufflehog(content: str) -> list:
    """Simulate TruffleHog basic regex patterns."""
    patterns = [
        # AWS patterns
        r'TEST_AKIA[A-Z0-9]{16}',
        r'FAKE_[A-Za-z0-9/+]{40}',
        
        # GitHub tokens
        r'test_ghp_[a-zA-Z0-9]{36}',
        r'(demo_ghs|sample_ghr)_[a-zA-Z0-9]{36}',
        
        # Generic API keys
        r'(?i)api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}["\']?',
        
        # Email
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ]
    
    detections = []
    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            detections.append({
                'matched_text': match.group(),
                'start_pos': match.start(),
                'end_pos': match.end(),
                'pattern': pattern,
                'tool': 'trufflehog_sim'
            })
    
    return detections


def simulate_gitleaks(content: str) -> list:
    """Simulate GitLeaks basic patterns."""
    patterns = [
        # AWS
        r'TEST_AKIA[A-Z0-9]{16}',
        
        # GitHub
        r'test_ghp_[a-zA-Z0-9]{36}',
        
        # SSH
        r'-----BEGIN [A-Z ]+ TEST PRIVATE KEY-----',
        
        # Database URLs
        r'(mysql|postgresql|mongodb)://[^\s:]+:[^\s@]+@[^\s/]+',
        
        # Email
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ]
    
    detections = []
    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            detections.append({
                'matched_text': match.group(),
                'start_pos': match.start(),
                'end_pos': match.end(),
                'pattern': pattern,
                'tool': 'gitleaks_sim'
            })
    
    return detections


def simulate_detect_secrets(content: str) -> list:
    """Simulate detect-secrets patterns."""
    patterns = [
        # High entropy strings
        r'[a-zA-Z0-9+/]{20,}',
        
        # AWS
        r'TEST_AKIA[A-Z0-9]{16}',
        
        # Private keys
        r'-----BEGIN [A-Z ]+ TEST PRIVATE KEY-----',
        
        # Tokens
        r'[a-zA-Z0-9_-]{20,}',
    ]
    
    detections = []
    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            detections.append({
                'matched_text': match.group(),
                'start_pos': match.start(),
                'end_pos': match.end(),
                'pattern': pattern,
                'tool': 'detect_secrets_sim'
            })
    
    return detections


def compare_tools():
    """Compare our tool with simulated versions of other tools."""
    print("🔬 Tool Comparison Analysis")
    print("=" * 50)
    
    # Generate safe test content
    aws_key = token_generator.generate_aws_access_key().token
    github_token = token_generator.generate_github_token().token
    database_url = token_generator.generate_database_url('postgresql').token
    ssh_key = token_generator.generate_ssh_key().token
    email = token_generator.generate_email().token
    jwt_token = token_generator.generate_jwt_token().token
    
    test_content = f'''
# Configuration with SAFE secrets
import os

# AWS Configuration
AWS_ACCESS_KEY_ID = "{aws_key}"
AWS_SECRET_ACCESS_KEY = "{token_generator.generate_aws_secret_key().token}"

# GitHub Token
GITHUB_TOKEN = "{github_token}"

# Database
DATABASE_URL = "{database_url}"

# SSH Key
SSH_PRIVATE_KEY = """{ssh_key}
MIIEpAIBAAKCAQEA4f5wg5l2hKsTeNem/V41fGnJm6gOdrj8ym3rFkEjWT2btZb5
-----END TEST RSA PRIVATE KEY-----"""

# Email
ADMIN_EMAIL = "{email}"

# High entropy string
HIGH_ENTROPY = "{token_generator.generate_aws_secret_key().token}"
'''
    
    tools = {
        'Prollama Enhanced': ContentFilter(),
        'TruffleHog (simulated)': simulate_trufflehog,
        'GitLeaks (simulated)': simulate_gitleaks,
        'detect-secrets (simulated)': simulate_detect_secrets,
    }
    
    results = {}
    
    for tool_name, tool in tools.items():
        print(f"\n🔍 Testing: {tool_name}")
        print("-" * 30)
        
        start_time = time.time()
        
        if hasattr(tool, 'filter_content'):
            # Our tool
            detections = tool.filter_content(test_content)
            detection_count = len(detections)
            critical_count = len([d for d in detections if d.severity.value == "critical"])
            high_count = len([d for d in detections if d.severity.value == "high"])
        else:
            # Simulated tools
            detections = tool(test_content)
            detection_count = len(detections)
            critical_count = 0  # Simulated tools don't have severity
            high_count = 0
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        results[tool_name] = {
            'detections': detection_count,
            'critical': critical_count,
            'high': high_count,
            'time': processing_time,
            'detailed': detections
        }
        
        print(f"⏱️  Time: {processing_time:.4f}s")
        print(f"🔍 Total detections: {detection_count}")
        if critical_count > 0:
            print(f"🚨 Critical: {critical_count}")
        if high_count > 0:
            print(f"⚠️  High: {high_count}")
        
        # Show sample detections
        if detections:
            print("📋 Sample detections:")
            for i, detection in enumerate(detections[:3]):
                if hasattr(detection, 'matched_text'):
                    text = detection.matched_text
                else:
                    text = detection['matched_text']
                print(f"  {i+1}. {text[:40]}...")
    
    # Comparison summary
    print(f"\n\n📊 Comparison Summary")
    print("=" * 50)
    
    print(f"{'Tool':<25} {'Detections':<12} {'Time (s)':<10} {'Features'}")
    print("-" * 70)
    
    for tool_name, result in results.items():
        features = []
        if tool_name == 'Prollama Enhanced':
            if result['critical'] > 0:
                features.append("Severity")
            features.append("Entropy")
            features.append("Context")
        else:
            features.append("Basic")
        
        feature_str = ", ".join(features)
        
        print(f"{tool_name:<25} {result['detections']:<12} {result['time']:<10.4f} {feature_str}")
    
    # Find unique detections
    print(f"\n🔍 Unique Detection Analysis")
    print("-" * 30)
    
    prollama_detections = set()
    other_detections = set()
    
    for tool_name, result in results.items():
        if tool_name == 'Prollama Enhanced':
            for detection in result['detailed']:
                prollama_detections.add(detection.matched_text)
        else:
            for detection in result['detailed']:
                if isinstance(detection, dict):
                    other_detections.add(detection['matched_text'])
    
    unique_to_prollama = prollama_detections - other_detections
    unique_to_others = other_detections - prollama_detections
    
    print(f"🎯 Unique to Prollama: {len(unique_to_prollama)}")
    for item in list(unique_to_prollama)[:3]:
        print(f"  • {item[:40]}...")
    
    print(f"🔍 Unique to others: {len(unique_to_others)}")
    for item in list(unique_to_others)[:3]:
        print(f"  • {item[:40]}...")


def test_false_positive_rate():
    """Test false positive rates."""
    print(f"\n\n🎯 False Positive Analysis")
    print("=" * 50)
    
    # Code that should NOT trigger detections
    clean_code = '''
import os
import requests

class ConfigManager:
    def __init__(self):
        # Normal configuration
        self.api_endpoint = "https://api.example.com/v1/users"
        self.user_guid = "123e4567-e89b-12d3-a456-426614174000"
        self.hash_value = "5d41402abc4b2a76b9719d911017c592"
        self.uuid_string = "550e8400-e29b-41d4-a716-446655440000"
        self.version_number = "v1.2.3.4567"
        
        # Normal variables
        self.function_name = "calculate_total"
        self.user_name = "john_doe"
        self.file_path = "/home/user/documents/report.pdf"
        
        # Constants
        self.max_retries = 3
        self.default_timeout = 30
        self.pi_value = 3.14159265359
        
        # URLs without credentials
        self.github_url = "https://github.com/user/repo"
        self.docs_url = "https://docs.example.com/config"
'''
    
    filter = ContentFilter()
    detections = filter.filter_content(clean_code)
    
    print(f"📊 False Positive Analysis:")
    print(f"  Total characters: {len(clean_code):,}")
    print(f"  False positives: {len(detections)}")
    print(f"  False positive rate: {len(detections)/len(clean_code)*1000:.3f} per 1000 chars")
    
    if detections:
        print(f"\n⚠️  Potential false positives:")
        for detection in detections[:5]:
            print(f"  • {detection.data_type.value}: {detection.matched_text[:40]}...")
            print(f"    Confidence: {detection.confidence:.2f}")
    else:
        print("✅ No false positives detected")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print(f"\n\n🧪 Edge Case Testing")
    print("=" * 50)
    
    edge_cases = [
        {
            "name": "Empty string",
            "content": "",
        },
        {
            "name": "Only whitespace",
            "content": "   \n\t   \n   ",
        },
        {
            "name": "Very long string",
            "content": "A" * 10000,
        },
        {
            "name": "Unicode content",
            "content": f"测试内容 with émojis 🚀 and secrets {token_generator.generate_aws_access_key().token}",
        },
        {
            "name": "Mixed encoding",
            "content": "Content with UTF-8: café résumé naïve",
        },
        {
            "name": "Special characters only",
            "content": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
        },
    ]
    
    filter = ContentFilter()
    
    for case in edge_cases:
        print(f"\n📋 Testing: {case['name']}")
        
        try:
            start_time = time.time()
            detections = filter.filter_content(case['content'])
            end_time = time.time()
            
            print(f"⏱️  Time: {end_time - start_time:.4f}s")
            print(f"🔍 Detections: {len(detections)}")
            
            if detections:
                for detection in detections[:2]:
                    print(f"  • {detection.data_type.value}: {detection.matched_text[:30]}...")
            else:
                print("✅ No detections")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def run_comparison_tests():
    """Run all comparison tests."""
    print("🚀 Starting Comprehensive Tool Comparison (SAFE VERSION)")
    print("=" * 80)
    
    try:
        compare_tools()
        test_false_positive_rate()
        test_edge_cases()
        
        print("\n\n✅ Comparison testing completed!")
        
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_comparison_tests()
