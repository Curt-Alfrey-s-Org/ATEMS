#!/bin/bash
# ATEMS PostgreSQL Migration Verification
# Run this script to verify the migration was successful

set -e

echo "============================================"
echo "ATEMS PostgreSQL Migration Verification"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check functions
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 exists"
        return 0
    else
        echo -e "${RED}❌${NC} $1 missing"
        return 1
    fi
}

check_string_in_file() {
    if grep -q "$2" "$1" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} $1 contains '$2'"
        return 0
    else
        echo -e "${RED}❌${NC} $1 missing '$2'"
        return 1
    fi
}

echo "Checking files..."
echo ""

# Files that should exist
echo "Created files:"
check_file "docker-compose.yml"
check_file "init-db.sql"
check_file "deploy_atems_postgres.sh"
check_file "POSTGRESQL_MIGRATION.md"
check_file "POSTGRESQL_MIGRATION_SUMMARY.md"
echo ""

echo "Modified files:"
check_file "requirements.txt"
check_file ".env"
check_file ".env.example"
check_file "extensions.py"
check_file "gunicorn.conf.py"
check_file "ROADMAP.md"
check_file "README.md"
echo ""

# Content checks
echo "Content verification:"
check_string_in_file "requirements.txt" "psycopg2-binary"
check_string_in_file ".env" "postgresql://"
check_string_in_file ".env" "POSTGRES_PASSWORD"
check_string_in_file "extensions.py" "pool_pre_ping"
check_string_in_file "gunicorn.conf.py" "default_workers"
check_string_in_file "docker-compose.yml" "atems-postgres"
check_string_in_file "docker-compose.yml" "postgres:16-alpine"
check_string_in_file "ROADMAP.md" "PostgreSQL Migration"
echo ""

# Docker-compose validation
echo "Docker Compose validation:"
if docker-compose config > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} docker-compose.yml is valid"
else
    echo -e "${RED}❌${NC} docker-compose.yml has errors"
fi
echo ""

# Check if traefik network exists
echo "Network check:"
if docker network inspect traefik_traefik > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} traefik_traefik network exists"
else
    echo -e "${YELLOW}⚠️${NC}  traefik_traefik network not found (will be created if external: false)"
fi
echo ""

# Model compatibility check
echo "Model compatibility:"
if ! grep -r "metadata\|Metadata" models/*.py 2>/dev/null | grep -v "# " | grep -v "__pycache__"; then
    echo -e "${GREEN}✅${NC} No reserved column names (metadata) found in models"
else
    echo -e "${YELLOW}⚠️${NC}  Found potential reserved column names"
fi
echo ""

# Summary
echo "============================================"
echo "Migration Verification Complete"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Review .env file and set secure passwords"
echo "  2. Run: ./deploy_atems_postgres.sh"
echo "  3. Access: http://localhost:5000"
echo "  4. Login: admin/admin123"
echo ""
echo "Documentation:"
echo "  - POSTGRESQL_MIGRATION.md (comprehensive guide)"
echo "  - POSTGRESQL_MIGRATION_SUMMARY.md (quick reference)"
echo "  - docker-compose.yml (service definitions)"
echo ""
