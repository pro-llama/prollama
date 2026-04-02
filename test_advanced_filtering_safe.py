#!/usr/bin/env python3
"""Advanced testing suite for content filtering system using SAFE tokens."""

import time
import random
import string
from pathlib import Path
from typing import List, Dict, Any

from prollama.security.content_filter import ContentFilter, DataType, SeverityLevel
from prollama.anonymizer.enhanced_layer import EnhancedAnonymizer, anonymize_code
from prollama.testing.token_generators import token_generator


def generate_test_data():
    """Generate comprehensive test data with SAFE tokens."""
    test_cases = []
    
    # Generate safe tokens for testing
    aws_access_key = token_generator.generate_aws_access_key().token
    aws_secret_key = token_generator.generate_aws_secret_key().token
    github_token = token_generator.generate_github_token().token
    slack_token = token_generator.generate_slack_token().token
    ssh_key = token_generator.generate_ssh_key().token
    email = token_generator.generate_email().token
    phone = "+1-555-TEST-1234"
    jwt_token = token_generator.generate_jwt_token().token
    database_url = token_generator.generate_database_url('postgresql').token
    redis_url = token_generator.generate_database_url('redis').token
    credit_card = token_generator.generate_credit_card().token
    
    # Edge case 1: Mixed content with multiple secrets
    test_cases.append({
        "name": "Mixed Secrets",
        "content": f'''
# Configuration file with secrets
import os

# AWS Configuration
AWS_ACCESS_KEY_ID = "{aws_access_key}"
AWS_SECRET_ACCESS_KEY = "{aws_secret_key}"

# Database
DATABASE_URL = "{database_url}"
REDIS_URL = "{redis_url}"

# API Keys
GITHUB_TOKEN = "{github_token}"
SLACK_TOKEN = "{slack_token}"

# Contact info
ADMIN_EMAIL = "{email}"
SUPPORT_PHONE = "{phone}"

# SSH Key
SSH_PRIVATE_KEY = """{ssh_key}
MIIEpAIBAAKCAQEA4f5wg5l2hKsTeNem/V41fGnJm6gOdrj8ym3rFkEjWT2btZb5
-----END TEST RSA PRIVATE KEY-----"""

# Payment
CREDIT_CARD = "{credit_card}"
''',
        "expected_detections": 10,
        "expected_critical": 3,
    })
    
    # Edge case 2: False positives testing
    test_cases.append({
        "name": "False Positives Test",
        "content": '''
# These should NOT be flagged as secrets
API_ENDPOINT = "https://api.example.com/v1/users"
USER_GUID = "123e4567-e89b-12d3-a456-426614174000"
HASH_VALUE = "5d41402abc4b2a76b9719d911017c592"
UUID_STRING = "550e8400-e29b-41d4-a716-446655440000"
VERSION_NUMBER = "v1.2.3.4567"
BUILD_HASH = "abc123def456"

# Normal variables
function_name = "calculate_total"
user_name = "john_doe"
file_path = "/home/user/documents/report.pdf"

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
PI_VALUE = 3.14159265359
''',
        "expected_detections": 0,
        "expected_critical": 0,
    })
    
    # Edge case 3: Obfuscated secrets
    test_cases.append({
        "name": "Obfuscated Secrets",
        "content": f'''
# Secrets with various obfuscations
api_key_1 = "{aws_access_key}"  # Direct
api_key_2 = '{aws_access_key}'   # Single quotes
api_key_3 = """{aws_access_key}""" # Triple quotes

# Split secrets
key_part1 = "TEST_AKIA"
key_part2 = "k3N6Dole9CK"
full_key = key_part1 + key_part2

# Base64 encoded (should still catch high entropy)
encoded_secret = "QUtJQUlPU0ZPRE5ORVhBTVBMRSUzRCUzRA=="

# Comments with secrets
# TODO: Replace {aws_access_key} with env var
# FIXME: Don't commit {github_token}
''',
        "expected_detections": 6,
        "expected_critical": 2,
    })
    
    # Edge case 4: Large file simulation
    large_content = ""
    for i in range(1000):
        large_content += f"variable_{i} = 'value_{i}'\n"
        if i % 100 == 0:
            # Insert secrets every 100 lines
            large_content += f"secret_key_{i} = '{token_generator.generate_aws_access_key().token}'\n"
            large_content += f"user_email_{i} = '{token_generator.generate_email().token}'\n"
    
    test_cases.append({
        "name": "Large File (1000 lines)",
        "content": large_content,
        "expected_detections": 20,  # 10 AWS keys + 10 emails
        "expected_critical": 10,
    })
    
    # Edge case 5: Unicode and special characters
    test_cases.append({
        "name": "Unicode and Special Characters",
        "content": f'''
# Unicode content
user_email = "{email}"
admin_name = "José García"
api_key = "{aws_access_key}"

# Special characters in context
password = "p@ssw0rd123!"
token = "{github_token}"

# International phone numbers
phone_uk = "+44-20-7946-0958"
phone_de = "+49-30-12345678"
phone_fr = "+33-1-42-86-83-26"
''',
        "expected_detections": 5,
        "expected_critical": 2,
    })
    
    return test_cases


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("🧪 Testing Edge Cases and Boundary Conditions")
    print("=" * 60)
    
    filter = ContentFilter()
    test_cases = generate_test_data()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        start_time = time.time()
        detections = filter.filter_content(test_case['content'])
        end_time = time.time()
        
        # Count by severity
        critical_count = len([d for d in detections if d.severity == SeverityLevel.CRITICAL])
        high_count = len([d for d in detections if d.severity == SeverityLevel.HIGH])
        
        print(f"⏱️  Processing time: {end_time - start_time:.3f}s")
        print(f"📊 Total detections: {len(detections)} (Expected: {test_case['expected_detections']})")
        print(f"🚨 Critical: {critical_count} (Expected: {test_case['expected_critical']})")
        print(f"⚠️  High: {high_count}")
        
        # Check if expectations match
        if len(detections) == test_case['expected_detections']:
            print("✅ Detection count matches expectation")
        else:
            print("❌ Detection count mismatch")
        
        if critical_count == test_case['expected_critical']:
            print("✅ Critical count matches expectation")
        else:
            print("❌ Critical count mismatch")
        
        # Show sample detections
        if detections:
            print("\n🔍 Sample detections:")
            for detection in detections[:3]:
                print(f"  • {detection.data_type.value}: {detection.matched_text[:50]}...")
                print(f"    Severity: {detection.severity.value}, Confidence: {detection.confidence:.2f}")


def test_performance():
    """Test performance with various content sizes."""
    print("\n\n🚀 Performance Testing")
    print("=" * 60)
    
    filter = ContentFilter()
    
    # Test different content sizes
    sizes = [100, 1000, 5000, 10000, 50000]
    
    for size in sizes:
        # Generate content with secrets
        content = ""
        for i in range(size):
            content += f"line_{i}: some content here\n"
            if i % (size // 10) == 0:  # Add secrets at 10% intervals
                content += f"secret_{i}: {token_generator.generate_aws_access_key().token}\n"
                content += f"email_{i}: {token_generator.generate_email().token}\n"
        
        start_time = time.time()
        detections = filter.filter_content(content)
        end_time = time.time()
        
        processing_time = end_time - start_time
        chars_per_second = len(content) / processing_time if processing_time > 0 else float('inf')
        
        print(f"\n📊 Size: {size:,} characters")
        print(f"⏱️  Time: {processing_time:.3f}s")
        print(f"🚀 Speed: {chars_per_second:,.0f} chars/sec")
        print(f"🔍 Detections: {len(detections)}")


def test_stress():
    """Stress test with high volume of secrets."""
    print("\n\n💪 Stress Testing")
    print("=" * 60)
    
    filter = ContentFilter()
    
    # Generate content with many different secret types
    secret_types = [
        ("AWS_KEY", token_generator.generate_aws_access_key().token),
        ("GITHUB_TOKEN", token_generator.generate_github_token().token),
        ("EMAIL", token_generator.generate_email().token),
        ("PHONE", "+1-555-TEST-1234"),
        ("JWT", token_generator.generate_jwt_token().token),
        ("SSH_KEY", token_generator.generate_ssh_key().token),
        ("CREDIT_CARD", token_generator.generate_credit_card().token),
        ("DATABASE_URL", token_generator.generate_database_url('postgresql').token),
    ]
    
    # Create content with 100 secrets
    content = ""
    for i in range(100):
        secret_type, secret_value = random.choice(secret_types)
        content += f"{secret_type}_{i}: {secret_value}\n"
    
    start_time = time.time()
    detections = filter.filter_content(content)
    end_time = time.time()
    
    print(f"📊 Processed 100 secrets in {end_time - start_time:.3f}s")
    print(f"🔍 Detected: {len(detections)} secrets")
    print(f"📈 Average: {end_time - start_time:.4f}s per secret")
    
    # Verify all were detected
    if len(detections) >= 80:  # Allow some margin for edge cases
        print("✅ High detection rate achieved")
    else:
        print("❌ Detection rate below expected")


def test_unicode_and_encoding():
    """Test Unicode and various encoding scenarios."""
    print("\n\n🌍 Unicode and Encoding Tests")
    print("=" * 60)
    
    filter = ContentFilter()
    
    unicode_test_cases = [
        {
            "name": "European Characters",
            "content": f'''
# European content
email_fr = "françois.müller@example.fr"
email_de = "josef.schmidt@example.de"
api_key = "{token_generator.generate_aws_access_key().token}"
phone_de = "+49-30-12345678"
''',
        },
        {
            "name": "Asian Characters",
            "content": f'''
# Asian content
user_jp = "ユーザー@example.jp"
admin_cn = "管理员@example.cn"
token = "{token_generator.generate_github_token().token}"
''',
        },
        {
            "name": "Mixed Scripts",
            "content": f'''
# Mixed scripts
comment_ru = "Это комментарий на русском"
api_key_1 = "{token_generator.generate_aws_access_key().token}"
email_ar = "مستخدم@example.com"
token_sl = "{token_generator.generate_slack_token().token}"
''',
        },
        {
            "name": "Emojis and Symbols",
            "content": f'''
# Content with emojis
config_🔑 = "{token_generator.generate_aws_access_key().token}"
user_📧 = "{token_generator.generate_email().token}"
token_🎫 = "{token_generator.generate_github_token().token}"
status_✅ = "active"
''',
        },
    ]
    
    for test_case in unicode_test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        try:
            detections = filter.filter_content(test_case['content'])
            print(f"✅ Successfully processed {len(detections)} detections")
            
            for detection in detections:
                print(f"  • {detection.data_type.value}: {detection.matched_text[:30]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def test_concurrent_processing():
    """Test concurrent processing scenarios."""
    print("\n\n⚡ Concurrent Processing Tests")
    print("=" * 60)
    
    import threading
    import queue
    
    filter = ContentFilter()
    results = queue.Queue()
    
    def process_content(content_id: int, content: str):
        """Worker function for concurrent processing."""
        try:
            start_time = time.time()
            detections = filter.filter_content(content)
            end_time = time.time()
            
            results.put({
                'id': content_id,
                'detections': len(detections),
                'time': end_time - start_time,
                'success': True
            })
        except Exception as e:
            results.put({
                'id': content_id,
                'error': str(e),
                'success': False
            })
    
    # Create multiple content pieces
    contents = []
    for i in range(10):
        content = f"# Content {i}\n"
        content += f"api_key_{i} = {token_generator.generate_aws_access_key().token}\n"
        content += f"email_{i} = {token_generator.generate_email().token}\n"
        contents.append(content)
    
    # Process concurrently
    threads = []
    start_time = time.time()
    
    for i, content in enumerate(contents):
        thread = threading.Thread(target=process_content, args=(i, content))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    
    # Collect results
    successful = 0
    failed = 0
    total_detections = 0
    
    while not results.empty():
        result = results.get()
        if result['success']:
            successful += 1
            total_detections += result['detections']
        else:
            failed += 1
            print(f"❌ Thread {result['id']} failed: {result['error']}")
    
    print(f"⏱️  Total time: {end_time - start_time:.3f}s")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"🔍 Total detections: {total_detections}")
    print(f"📊 Average per thread: {total_detections / successful if successful > 0 else 0:.1f}")


def test_memory_usage():
    """Test memory usage with large content."""
    print("\n\n💾 Memory Usage Tests")
    print("=" * 60)
    
    import sys
    import gc
    
    filter = ContentFilter()
    
    # Test progressively larger content
    sizes = [1000, 5000, 10000, 50000]
    
    for size in sizes:
        # Generate large content
        content = ""
        for i in range(size):
            content += f"line_{i}: content with secret {token_generator.generate_aws_access_key().token}\n"
        
        # Measure memory before
        gc.collect()
        objects_before = len(gc.get_objects())
        
        # Process content
        start_time = time.time()
        detections = filter.filter_content(content)
        end_time = time.time()
        
        # Measure memory after
        objects_after = len(gc.get_objects())
        
        print(f"\n📁 Size: {size:,} lines")
        print(f"⏱️  Time: {end_time - start_time:.3f}s")
        print(f"🔍 Detections: {len(detections)}")
        print(f"💾 Objects created: {objects_after - objects_before:,}")
        
        # Clean up
        del content
        del detections


def run_comprehensive_tests():
    """Run all advanced tests."""
    print("🚀 Starting Advanced Content Filter Tests (SAFE VERSION)")
    print("=" * 80)
    
    try:
        test_edge_cases()
        test_performance()
        test_stress()
        test_unicode_and_encoding()
        test_concurrent_processing()
        test_memory_usage()
        
        print("\n\n✅ All advanced tests completed successfully!")
        
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_comprehensive_tests()
