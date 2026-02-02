#!/bin/bash
# Run ATEMS test suite. Double-click or run from terminal.
cd "$(dirname "$0")"
if [ -d .venv ]; then
  source .venv/bin/activate
elif [ -d venv ]; then
  source venv/bin/activate
fi
echo "=== ATEMS Self-Test Suite ==="
./run_selftest.sh || true
echo ""
read -p "Press Enter to close..."
