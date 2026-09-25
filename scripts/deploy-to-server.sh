#!/bin/bash
# Deploy ATEMS: build frontend (if present) and rsync to server.
# Run from ATEMS repo root.
#
# Usage:
#   ./scripts/deploy-to-server.sh                    # build only
#   ./scripts/deploy-to-server.sh ansible@192.168.0.105   # build + rsync to server
#
# Any error (npm missing, npm ci/build failure, rsync failure) stops the
# script with a non-zero exit code and the tool's own error output. To deploy
# without building the frontend on purpose, set SKIP_FRONTEND_BUILD=1.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_ROOT"

echo "=========================================="
echo "  ATEMS — Deploy (build + optional sync)"
echo "=========================================="
echo "App root: $APP_ROOT"
echo ""

# Build frontend if present
if [ "${SKIP_FRONTEND_BUILD:-0}" = "1" ]; then
  echo "SKIP_FRONTEND_BUILD=1 — skipping frontend build."
elif [ -d frontend ] && [ -f frontend/package.json ]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: frontend/ exists but npm is not installed. Install Node.js/npm," >&2
    echo "       or re-run with SKIP_FRONTEND_BUILD=1 to deploy without building it." >&2
    exit 1
  fi
  echo "Building frontend..."
  if ! (cd frontend && npm ci && npm run build); then
    echo "ERROR: frontend build failed (see npm output above). Aborting deploy." >&2
    exit 1
  fi
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
  "$APP_ROOT/" "$SSH_TARGET:~/$REMOTE_DIR/" || {
  rc=$?
  echo "ERROR: rsync failed with exit code $rc (see rsync/ssh output above)." >&2
  echo "       Fix SSH/rsync access, or use git clone on the server." >&2
  exit "$rc"
}

echo ""
echo "Next on server (SSH to $SSH_TARGET):"
echo "  cd ~/atems"
echo "  source .venv/bin/activate   # or create: python3 -m venv .venv && pip install -r requirements.txt"
echo "  cp .env.example .env && <edit .env>"
echo "  flask db upgrade"
echo "  sudo systemctl restart atems   # after Nginx + systemd setup"
echo "  See web-sites-server/DEPLOY_NOW.md for full steps."
