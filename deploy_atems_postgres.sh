#!/bin/bash
# Deploy ATEMS with PostgreSQL
# Usage: ./deploy_atems_postgres.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$SCRIPT_DIR"
cd "$APP_ROOT"

echo "============================================"
echo "ATEMS PostgreSQL Deployment Script"
echo "============================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

COMPOSE_CMD=""
if docker compose version &>/dev/null 2>&1; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE_CMD="docker-compose"
else
  echo -e "${RED}Error: docker compose or docker-compose is not installed${NC}"
  exit 1
fi

ENV_FILE="$APP_ROOT/.env"
COMPOSE_ENV_ARGS=()
[ -f "$ENV_FILE" ] && COMPOSE_ENV_ARGS+=(--env-file "$ENV_FILE")
# shellcheck disable=SC1091
. "$APP_ROOT/scripts/export_compose_uid_gid.sh"
write_compose_host_user_env "$APP_ROOT"
COMPOSE_ENV_ARGS+=(--env-file "$APP_ROOT/.env.compose-host-user")

compose() {
  $COMPOSE_CMD "${COMPOSE_ENV_ARGS[@]}" "$@"
}

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env and set POSTGRES_PASSWORD, SECRET_KEY and ADMIN_PASSWORD${NC}"
    echo -e "${YELLOW}Press Enter to continue after editing .env...${NC}"
    read
fi

# Check if PostgreSQL password is set
if grep -q "your_secure_password" .env || grep -q "changeme123" .env; then
    echo -e "${YELLOW}Warning: Using default/example PostgreSQL password${NC}"
    echo -e "${YELLOW}Recommendation: Set a secure password in .env${NC}"
fi

echo "Step 1: Building ATEMS Docker image..."
# TrueNAS hub: refresh build-contexts/wheels-bots before build (non-fatal).
ALFA_AI_ROOT="${ALFA_AI_ROOT:-$APP_ROOT/../alfa-ai}"
[ -f "$ALFA_AI_ROOT/scripts/sync-bot-wheels-preflight.sh" ] && \
  bash "$ALFA_AI_ROOT/scripts/sync-bot-wheels-preflight.sh" || true
compose build atems-api

echo ""
echo "Step 2: Starting PostgreSQL + ATEMS API..."
echo "  (docker compose up --wait blocks until service healthchecks pass; see docker-compose.yml)"
if ! compose up -d --wait atems-postgres atems-api; then
    echo -e "${RED}Error: compose up --wait failed${NC}"
    compose logs atems-postgres 2>/dev/null || true
    compose logs atems-api 2>/dev/null || true
    exit 1
fi
echo -e "${GREEN}PostgreSQL and ATEMS API are healthy.${NC}"

echo ""
echo "Step 3: Running database migrations..."
# The image has no FLASK_APP / app.py, so point the Flask CLI at atems:app explicitly.
flask_cli() {
    compose exec -T -e FLASK_APP=atems:app atems-api flask "$@"
}

# The app runs db.create_all() on startup, so a brand-new database already has every
# table but no alembic_version row; `flask db upgrade` would then fail on the initial
# CREATE TABLE. Detect that case: if the schema matches the models exactly, stamp it at
# head; if it differs, stop and let the operator decide (never guess).
set +e
compose exec -T atems-api python - <<'PY'
import sys
from sqlalchemy import inspect, text
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from atems import app
from extensions import db

with app.app_context():
    insp = inspect(db.engine)
    if insp.has_table("alembic_version") and db.session.execute(
        text("SELECT version_num FROM alembic_version")
    ).first():
        print("Database is under migration control.")
        sys.exit(0)
    app_tables = set(db.metadata.tables) & set(insp.get_table_names())
    if not app_tables:
        print("Empty database: migrations will create the schema.")
        sys.exit(0)
    with db.engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), db.metadata)
    if not diff:
        print("Unversioned database whose schema matches the models: will stamp head.")
        sys.exit(10)
    print("Unversioned database whose schema does NOT match the models:", file=sys.stderr)
    for d in diff:
        print(f"  {d}", file=sys.stderr)
    sys.exit(2)
PY
db_state=$?
set -e

case "$db_state" in
  0) ;;
  10)
    if ! flask_cli db stamp head; then
        echo -e "${RED}Error: 'flask db stamp head' failed. Deployment aborted.${NC}"
        exit 1
    fi
    ;;
  2)
    echo -e "${RED}Error: the database has tables but no Alembic version, and its schema differs from the models (see above).${NC}"
    echo -e "${RED}Inspect it, then either migrate it by hand or run '$COMPOSE_CMD exec -e FLASK_APP=atems:app atems-api flask db stamp <revision>' and re-run this script.${NC}"
    exit 1
    ;;
  *)
    echo -e "${RED}Error: could not inspect the database migration state (exit $db_state). Deployment aborted.${NC}"
    compose logs --tail=50 atems-api 2>/dev/null || true
    exit 1
    ;;
esac

if ! flask_cli db upgrade; then
    echo -e "${RED}Error: database migration ('flask db upgrade') failed. Deployment aborted.${NC}"
    echo -e "${RED}The API container is already running the new code against the un-migrated schema; fix the migration and re-run this script.${NC}"
    compose logs --tail=50 atems-api 2>/dev/null || true
    exit 1
fi
echo -e "${GREEN}Database migrations applied.${NC}"

echo ""
echo "============================================"
echo -e "${GREEN}ATEMS Deployment Complete!${NC}"
echo "============================================"
echo ""
echo "Services:"
echo "  - PostgreSQL: localhost:5436"
echo "  - ATEMS API:  http://localhost:5000"
echo ""
echo "Login:"
echo "  - There are no default credentials. On first boot (empty database) the admin"
echo "    account is created from ADMIN_USERNAME / ADMIN_PASSWORD in .env."
echo ""
echo "Useful commands (from repo root; include --env-file .env and --env-file .env.compose-host-user if using user: in compose):"
echo "  - View logs:       $COMPOSE_CMD --env-file .env --env-file .env.compose-host-user logs -f atems-api"
echo "  - Stop services:   $COMPOSE_CMD --env-file .env --env-file .env.compose-host-user down"
echo "  - Restart:         $COMPOSE_CMD --env-file .env --env-file .env.compose-host-user restart atems-api"
echo "  - Database shell:  $COMPOSE_CMD --env-file .env --env-file .env.compose-host-user exec atems-postgres psql -U atems_user -d atems"
echo ""
echo -e "${GREEN}Deployment successful!${NC}"
