#!/usr/bin/env python3
"""Test content filtering on real project files."""

import subprocess
import time
from pathlib import Path
from prollama.security.content_filter import ContentFilter


def test_prollama_project():
    """Test filtering on prollama project files."""
    print("🔍 Testing Prollama Project Files")
    print("=" * 50)
    
    filter = ContentFilter()
    
    # Find Python files in prollama
    prollama_files = list(Path("/home/tom/github/pro-llama/prollama").rglob("*.py"))
    
    # Test a few representative files
    test_files = [
        "/home/tom/github/pro-llama/prollama/src/prollama/cli.py",
        "/home/tom/github/pro-llama/prollama/src/prollama/auth.py", 
        "/home/tom/github/pro-llama/prollama/src/prollama/config.py",
        "/home/tom/github/pro-llama/prollama/src/prollama/executor.py",
    ]
    
    total_detections = 0
    files_with_secrets = 0
    
    for file_path in test_files:
        if Path(file_path).exists():
            try:
                content = Path(file_path).read_text()
                detections = filter.filter_content(content)
                
                if detections:
                    files_with_secrets += 1
                    total_detections += len(detections)
                    
                    print(f"\n📁 {file_path}")
                    print(f"⚠️  {len(detections)} detections:")
                    
                    for detection in detections[:5]:  # Show first 5
                        print(f"  • {detection.data_type.value}: {detection.matched_text[:30]}...")
                        
                else:
                    print(f"✅ {file_path}: Clean")
                    
            except Exception as e:
                print(f"❌ {file_path}: Error - {e}")
    
    print(f"\n📊 Summary:")
    print(f"  Files tested: {len(test_files)}")
    print(f"  Files with secrets: {files_with_secrets}")
    print(f"  Total detections: {total_detections}")


def test_sample_projects():
    """Test filtering on sample project files."""
    print("\n\n🔍 Testing Sample Project Files")
    print("=" * 50)
    
    sample_files = [
        "/home/tom/github/pro-llama/2026/prollama/examples/sample_code/fintech_app.py",
        "/home/tom/github/pro-llama/2026/prollama/examples/sample_code/ml_pipeline.py",
        "/home/tom/github/pro-llama/2026/prollama/examples/sample_code/healthcare_app.py",
        "/home/tom/github/pro-llama/2026/prollama/examples/sample_code/api_secrets.py",
    ]
    
    filter = ContentFilter()
    
    for file_path in sample_files:
        if Path(file_path).exists():
            print(f"\n📁 {Path(file_path).name}")
            
            try:
                content = Path(file_path).read_text()
                detections = filter.filter_content(content)
                
                if detections:
                    print(f"⚠️  {len(detections)} detections found:")
                    
                    # Group by severity
                    critical = [d for d in detections if d.severity.value == "critical"]
                    high = [d for d in detections if d.severity.value == "high"]
                    medium = [d for d in detections if d.severity.value == "medium"]
                    
                    if critical:
                        print(f"  🚨 Critical ({len(critical)}):")
                        for d in critical[:3]:
                            print(f"    • {d.data_type.value}: {d.matched_text[:30]}...")
                    
                    if high:
                        print(f"  ⚠️  High ({len(high)}):")
                        for d in high[:3]:
                            print(f"    • {d.data_type.value}: {d.matched_text[:30]}...")
                    
                    if medium:
                        print(f"  🔍 Medium ({len(medium)}):")
                        for d in medium[:3]:
                            print(f"    • {d.data_type.value}: {d.matched_text[:30]}...")
                
                else:
                    print("✅ No detections")
                    
            except Exception as e:
                print(f"❌ Error: {e}")


def test_cli_integration():
    """Test CLI integration on various files."""
    print("\n\n🧪 Testing CLI Integration")
    print("=" * 50)
    
    test_files = [
        "test_secrets_sample.py",
        "/home/tom/github/pro-llama/2026/prollama/examples/sample_code/api_secrets.py",
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            print(f"\n📁 Testing: {file_path}")
            
            try:
                # Test basic anonymization
                result = subprocess.run(
                    [".venv/bin/prollama", "anonymize", file_path],
                    capture_output=True,
                    text=True,
                    cwd="/home/tom/github/pro-llama/prollama"
                )
                
                if result.returncode == 0:
                    print("✅ Basic anonymization: Success")
                else:
                    print(f"❌ Basic anonymization: {result.stderr}")
                
                # Test with secret filtering
                result = subprocess.run(
                    [".venv/bin/prollama", "anonymize", file_path, "--filter-secrets"],
                    capture_output=True,
                    text=True,
                    cwd="/home/tom/github/pro-llama/prollama"
                )
                
                if result.returncode == 0:
                    print("✅ Secret filtering: Success")
                    
                    # Count anonymized items in output
                    if "[SECRET_" in result.stdout or "[TOKEN_" in result.stdout:
                        secret_count = result.stdout.count("[SECRET_") + result.stdout.count("[TOKEN_") + result.stdout.count("[EMAIL_") + result.stdout.count("[CREDIT_CARD_")
                        print(f"🔍 Found {secret_count} filtered items")
                    else:
                        print("🔍 No filtered items detected")
                        
                else:
                    print(f"❌ Secret filtering: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ CLI test error: {e}")


def test_performance_on_real_files():
    """Test performance on real project files."""
    print("\n\n⚡ Performance Testing on Real Files")
    print("=" * 50)
    
    filter = ContentFilter()
    
    # Test on progressively larger files
    test_files = [
        "test_secrets_sample.py",  # Small (~2KB)
        "/home/tom/github/pro-llama/2026/prollama/examples/sample_code/api_secrets.py",  # Medium (~5KB)
        "/home/tom/github/pro-llama/prollama/src/prollama/cli.py",  # Large (~15KB)
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            try:
                content = Path(file_path).read_text()
                file_size = len(content)
                
                start_time = time.time()
                detections = filter.filter_content(content)
                end_time = time.time()
                
                processing_time = end_time - start_time
                chars_per_second = file_size / processing_time if processing_time > 0 else float('inf')
                
                print(f"\n📁 {Path(file_path).name}")
                print(f"📊 Size: {file_size:,} characters")
                print(f"⏱️  Time: {processing_time:.3f}s")
                print(f"🚀 Speed: {chars_per_second:,.0f} chars/sec")
                print(f"🔍 Detections: {len(detections)}")
                
            except Exception as e:
                print(f"❌ {file_path}: Error - {e}")


def run_real_project_tests():
    """Run all tests on real project files."""
    print("🚀 Testing Content Filter on Real Projects")
    print("=" * 80)
    
    try:
        test_prollama_project()
        test_sample_projects()
        test_cli_integration()
        test_performance_on_real_files()
        
        print("\n\n✅ Real project testing completed!")
        
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_real_project_tests()
