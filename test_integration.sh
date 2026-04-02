#!/bin/bash
# Test script for prollama + www proxy integration

echo "=== Testing prollama CLI with local anonymization ==="

# Test anonymization of sample files
for file in examples/sample_code/*.py; do
    echo "Testing: $file"
    prollama anonymize "$file" --level basic > /dev/null 2>&1 && echo "  ✓ basic OK" || echo "  ✗ basic FAIL"
    prollama anonymize "$file" --level full > /dev/null 2>&1 && echo "  ✓ full OK" || echo "  ✗ full FAIL"
done

echo ""
echo "=== Summary ==="
echo "Files tested: $(ls examples/sample_code/*.py | wc -l)"
echo "All tests completed"
