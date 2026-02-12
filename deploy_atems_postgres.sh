#!/bin/bash
# Deploy ATEMS with PostgreSQL
# Usage: ./deploy_atems_postgres.sh

set -e

echo "============================================"
echo "ATEMS PostgreSQL Deployment Script"
echo "============================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please edit .env and set POSTGRES_PASSWORD and SECRET_KEY${NC}"
    echo -e "${YELLOW}Press Enter to continue after editing .env...${NC}"
    read
fi

# Check if PostgreSQL password is set
if grep -q "your_secure_password" .env || grep -q "changeme123" .env; then
    echo -e "${YELLOW}Warning: Using default/example PostgreSQL password${NC}"
    echo -e "${YELLOW}Recommendation: Set a secure password in .env${NC}"
fi

echo "Step 1: Building ATEMS Docker image..."
docker-compose build atems-api

echo ""
echo "Step 2: Starting PostgreSQL..."
docker-compose up -d atems-postgres

echo ""
echo "Step 3: Waiting for PostgreSQL to be ready..."
sleep 5

# Wait for PostgreSQL health check
echo "Checking PostgreSQL health..."
retries=30
while [ $retries -gt 0 ]; do
    if docker-compose ps | grep -q "atems-postgres.*healthy"; then
        echo -e "${GREEN}PostgreSQL is ready!${NC}"
        break
    fi
    retries=$((retries - 1))
    echo "Waiting for PostgreSQL... ($retries retries left)"
    sleep 2
done

if [ $retries -eq 0 ]; then
    echo -e "${RED}Error: PostgreSQL failed to start${NC}"
    docker-compose logs atems-postgres
    exit 1
fi

echo ""
echo "Step 4: Starting ATEMS API..."
docker-compose up -d atems-api

echo ""
echo "Step 5: Waiting for ATEMS API to be ready..."
sleep 3

# Check if ATEMS is running
if docker-compose ps | grep -q "atems-api.*Up"; then
    echo -e "${GREEN}ATEMS API is running!${NC}"
else
    echo -e "${RED}Error: ATEMS API failed to start${NC}"
    docker-compose logs atems-api
    exit 1
fi

echo ""
echo "Step 6: Running database migrations..."
docker-compose exec -T atems-api flask db upgrade || {
    echo -e "${YELLOW}Note: Migrations may not exist yet. Creating tables with db.create_all()...${NC}"
    echo "Tables will be created automatically on first run."
}

echo ""
echo "============================================"
echo -e "${GREEN}ATEMS Deployment Complete!${NC}"
echo "============================================"
echo ""
echo "Services:"
echo "  - PostgreSQL: localhost:5436"
echo "  - ATEMS API:  http://localhost:5000"
echo ""
echo "Default credentials:"
echo "  - Username: admin"
echo "  - Password: admin123"
echo ""
echo "Useful commands:"
echo "  - View logs:       docker-compose logs -f atems-api"
echo "  - Stop services:   docker-compose down"
echo "  - Restart:         docker-compose restart atems-api"
echo "  - Database shell:  docker-compose exec atems-postgres psql -U atems_user -d atems"
echo ""
echo -e "${GREEN}Deployment successful!${NC}"
