#!/bin/bash
# Start ATEMS server. Double-click or run from terminal.
cd "$(dirname "$0")"
if [ -d .venv ]; then
  source .venv/bin/activate
elif [ -d venv ]; then
  source venv/bin/activate
fi
echo "Starting ATEMS at http://127.0.0.1:5000"
(sleep 3 && xdg-open http://127.0.0.1:5000 2>/dev/null) &
exec python atems.py
