#!/bin/bash
# Build ATEMS frontend on the server and optionally restart the service.
# Run from ATEMS root ON THE SERVER (~/atems).
#
# Usage:
#   ./scripts/build_on_server.sh           # build frontend only
#   ./scripts/build_on_server.sh --restart # build frontend then restart atems

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$APP_ROOT"

RESTART_ATEMS=
for arg in "$@"; do
  [ "$arg" = "--restart" ] || [ "$arg" = "-r" ] && RESTART_ATEMS=1 && break
done

echo "=========================================="
echo "  ATEMS — Build on server"
echo "=========================================="
echo "App root: $APP_ROOT"
echo ""

if [ ! -d frontend ] || [ ! -f frontend/package.json ]; then
  echo "No frontend/ — skipping build."
else
  if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
    echo "❌ Node.js and npm required. Install: sudo apt install nodejs npm"
    exit 1
  fi
  echo "Installing frontend deps..."
  (cd frontend && npm install --no-audit --no-fund -q)
  echo "Building frontend..."
  (cd frontend && npm run build) || { echo "❌ Frontend build failed."; exit 1; }
  echo "✅ frontend/dist → static/app"
fi
echo ""

if [ -n "$RESTART_ATEMS" ]; then
  if command -v systemctl &>/dev/null && systemctl is-active --quiet atems 2>/dev/null; then
    echo "Restarting atems..."
    sudo systemctl restart atems
    echo "✅ atems restarted."
  else
    echo "⚠️  atems service not running. Start manually: sudo systemctl start atems"
  fi
  echo ""
fi

echo "Done. https://atems.alfaquantumdynamics.com (hard-refresh if needed)"
