#!/bin/bash
# ATEMS deployment script - run on the server (e.g. /var/www/atems)
# Usage: ./scripts/deploy.sh [APP_DIR]
#   APP_DIR defaults to parent of this script (ATEMS project root)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${1:-$(dirname "$SCRIPT_DIR")}"
cd "$APP_DIR"

echo "=== ATEMS Deploy: $APP_DIR ==="

# Activate venv
if [ -d .venv ]; then
  source .venv/bin/activate
elif [ -d venv ]; then
  source venv/bin/activate
else
  echo "Error: No .venv or venv found. Create one first: python3 -m venv .venv"
  exit 1
fi

# Pull latest (if git repo)
if [ -d .git ]; then
  git pull --ff-only || true
fi

# Install dependencies
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Run migrations
flask db upgrade 2>/dev/null || true

# Build React frontend if frontend/ exists
if [ -d frontend ] && [ -f frontend/package.json ]; then
  (cd frontend && npm ci --omit=dev 2>/dev/null && npm run build 2>/dev/null) || true
fi

echo "=== Deploy complete ==="
echo "Restart the service: sudo systemctl restart atems"
