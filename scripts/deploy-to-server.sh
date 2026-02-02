#!/bin/bash
# Deploy ATEMS: build frontend (if present) and rsync to server.
# Run from ATEMS repo root.
#
# Usage:
#   ./scripts/deploy-to-server.sh                    # build only
#   ./scripts/deploy-to-server.sh ansible@192.168.0.105   # build + rsync to server

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_ROOT"

echo "=========================================="
echo "  ATEMS — Deploy (build + optional sync)"
echo "=========================================="
echo "App root: $APP_ROOT"
echo ""

# Build frontend if present
if [ -d frontend ] && [ -f frontend/package.json ]; then
  echo "Building frontend..."
  (cd frontend && npm install -q 2>/dev/null && npm run build 2>/dev/null) || {
    echo "Frontend build failed (or npm not installed). Skipping."
  }
  echo "OK"
else
  echo "No frontend/ — skipping build."
fi
echo ""

SSH_TARGET="${1:-}"
if [ -z "$SSH_TARGET" ]; then
  echo "No SSH target given. To sync to server: $0 ansible@192.168.0.105"
  echo "See web-sites-server/DEPLOY_NOW.md for full steps."
  exit 0
fi

REMOTE_DIR="atems"
echo "Syncing to $SSH_TARGET (remote: ~/$REMOTE_DIR/)..."
rsync -avz --delete \
  --exclude 'node_modules' \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude 'instance' \
  --exclude '*.db' \
  --exclude '*.log' \
  --exclude '.env' \
  "$APP_ROOT/" "$SSH_TARGET:~/$REMOTE_DIR/" 2>/dev/null || {
  echo "rsync failed. Use: git clone on server, or fix SSH/rsync."
  exit 1
}

echo ""
echo "Next on server (SSH to $SSH_TARGET):"
echo "  cd ~/atems"
echo "  source .venv/bin/activate   # or create: python3 -m venv .venv && pip install -r requirements.txt"
echo "  cp .env.example .env && <edit .env>"
echo "  flask db upgrade"
echo "  sudo systemctl restart atems   # after nginx + systemd setup"
echo "  See web-sites-server/DEPLOY_NOW.md for full steps."
