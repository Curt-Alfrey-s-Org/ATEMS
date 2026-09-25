#!/bin/bash
# ATEMS deployment script - run on the server (e.g. /var/www/atems)
# Usage: ./scripts/deploy.sh [APP_DIR]
#   APP_DIR defaults to parent of this script (ATEMS project root)
#
# Every step fails loudly: a failed git pull, pip install, migration or frontend
# build stops the deploy with a non-zero exit code (review 2026-09-25; these
# used to be hidden with `|| true` and `2>/dev/null`).
#
# Optional environment:
#   SKIP_GIT_PULL=1    do not run `git pull --ff-only`
#   SKIP_MIGRATIONS=1  do not run `flask db upgrade`
#   SKIP_FRONTEND=1    do not build frontend/ (React SPA -> static/app)
#   FLASK_APP          defaults to atems.py (needed for `flask db upgrade`)

set -euo pipefail

on_error() {
  local rc=$?
  echo "ERROR: deploy failed (exit $rc) at line $1: $2" >&2
  echo "Nothing was restarted. Fix the error above and re-run $0." >&2
  exit "$rc"
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${1:-$(dirname "$SCRIPT_DIR")}"
cd "$APP_DIR"

echo "=== ATEMS Deploy: $APP_DIR ==="

# Activate venv (activate scripts may reference unset variables, so relax -u here)
if [ -d .venv ]; then
  VENV_DIR=.venv
elif [ -d venv ]; then
  VENV_DIR=venv
else
  echo "Error: No .venv or venv found. Create one first: python3 -m venv .venv" >&2
  exit 1
fi
set +u
# shellcheck disable=SC1090,SC1091
source "$VENV_DIR/bin/activate"
set -u

# Pull latest (if git repo)
if [ -d .git ] && [ "${SKIP_GIT_PULL:-0}" != "1" ]; then
  echo "--- git pull --ff-only"
  if ! git pull --ff-only; then
    echo "Error: git pull --ff-only failed (local changes or diverged branch)." >&2
    echo "Resolve it, or re-run with SKIP_GIT_PULL=1 to deploy the current checkout." >&2
    exit 1
  fi
fi

# Install dependencies
echo "--- pip install"
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Run migrations
if [ "${SKIP_MIGRATIONS:-0}" != "1" ]; then
  echo "--- flask db upgrade"
  export FLASK_APP="${FLASK_APP:-atems.py}"
  if ! flask db upgrade; then
    echo "Error: database migration failed (see output above)." >&2
    echo "If this database was created by db.create_all() and has never been migrated," >&2
    echo "check the schema matches the models, then run once: FLASK_APP=atems.py flask db stamp head" >&2
    exit 1
  fi
fi

# Build React frontend if frontend/ exists.
# Full `npm ci` (not --omit=dev): the build needs devDependencies (vite, typescript).
if [ "${SKIP_FRONTEND:-0}" != "1" ] && [ -d frontend ] && [ -f frontend/package.json ]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Error: npm not found but frontend/ exists. Install Node.js >= 18 or re-run with SKIP_FRONTEND=1." >&2
    exit 1
  fi
  echo "--- frontend: npm ci && npm run build"
  (cd frontend && npm ci --no-audit --no-fund && npm run build)
fi

echo "=== Deploy complete ==="
echo "Restart the service: sudo systemctl restart atems"
