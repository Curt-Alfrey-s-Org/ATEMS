#!/bin/bash
# ATEMS Self-Test Runner
# Runs startup selftests + pytest (including error-pattern tests).
# Adapted from Rankings-Bot run_selftest / run_tests.
# Use this to catch errors before they show up in logs.

cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null || true

echo "=============================================="
echo "ATEMS Self-Test Suite"
echo "=============================================="
echo ""

echo "1. Startup self-tests..."
python -c "
from selftest.startup import run_startup_selftests
p, f, r = run_startup_selftests(app=None, logger=None)
for x in r:
    sym = '✓' if x.get('passed') else '✗'
    err = (': ' + str(x.get('error',''))[:60]) if not x.get('passed') else ''
    print('  ' + sym + ' ' + x['name'] + err)
print('')
print('  Result: ' + str(p) + '/' + str(p+f) + ' passed')
import sys
sys.exit(1 if f > 0 else 0)
"
STARTUP_EXIT=$?
if [ "$STARTUP_EXIT" -ne 0 ]; then
    echo "  Startup self-tests had failures (exit $STARTUP_EXIT)"
fi
echo ""

echo "2. Pytest (unit + integration + error patterns)..."
pytest tests/ -v --tb=short
PYTEST_EXIT=$?
echo ""

echo "=============================================="
if [ $STARTUP_EXIT -eq 0 ] && [ $PYTEST_EXIT -eq 0 ]; then
    echo "All self-tests passed."
    exit 0
else
    echo "Some tests failed. Review atems.log for runtime errors."
    exit 1
fi
