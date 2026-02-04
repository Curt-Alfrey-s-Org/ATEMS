#!/bin/bash
# Run ATEMS test suite (startup + pytest)
# Usage: ./run_tests.sh   or   bash run_tests.sh

set -e
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || true

echo "=== ATEMS Test Suite ==="
echo ""

echo "1. Startup tests..."
python tests/startup_test.py
echo ""

echo "2. Pytest (check-in/out, README claims)..."
pytest tests/ -v
echo ""

echo "=== All tests completed ==="
