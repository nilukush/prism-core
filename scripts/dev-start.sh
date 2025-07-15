#!/bin/bash

# PRISM Local Development Startup Script
# Simplifies starting the development environment

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting PRISM Development Environment${NC}"
echo "========================================"

# Check if .env exists, if not copy from .env.development
if [ ! -f .env ]; then
    echo -e "${YELLOW}📋 Creating .env from .env.development${NC}"
    cp .env.development .env
fi

# Parse command line arguments
PROFILE=""
DEBUG_TOOLS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG_TOOLS=true
            PROFILE="--profile debug"
            shift
            ;;
        --email)
            PROFILE="$PROFILE --profile email"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --debug    Enable debug tools (Redis Commander, PGAdmin)"
            echo "  --email    Enable email testing (MailHog)"
            echo "  --help     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                  # Start basic services"
            echo "  $0 --debug          # Start with debug tools"
            echo "  $0 --debug --email  # Start with all tools"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Start services
echo -e "${BLUE}🐳 Starting Docker services...${NC}"
docker compose -f docker-compose.yml -f docker-compose.dev.yml $PROFILE up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check service health
echo -e "${BLUE}🔍 Checking service status...${NC}"
docker compose ps

# Check backend health
if curl -s http://localhost:8100/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Backend is still starting up...${NC}"
fi

# Display access information
echo ""
echo -e "${GREEN}🎉 PRISM Development Environment Started!${NC}"
echo "========================================"
echo ""
echo "Access Points:"
echo "  Frontend:    http://localhost:3100"
echo "  Backend API: http://localhost:8100"
echo "  API Docs:    http://localhost:8100/docs"

if [ "$DEBUG_TOOLS" = true ]; then
    echo ""
    echo "Debug Tools:"
    echo "  Redis Commander: http://localhost:8081"
    echo "  PGAdmin:         http://localhost:5050"
    echo "    Email: admin@local.dev"
    echo "    Password: admin"
fi

if [[ "$PROFILE" == *"email"* ]]; then
    echo ""
    echo "Email Testing:"
    echo "  MailHog UI: http://localhost:8025"
fi

echo ""
echo "Login Credentials:"
echo "  Email:    nilukush@gmail.com"
echo "  Password: n1i6Lu!8"
echo ""
echo "Commands:"
echo "  View logs:    docker compose logs -f backend"
echo "  Stop all:     docker compose -f docker-compose.yml -f docker-compose.dev.yml down"
echo "  Reset DB:     docker volume rm prism-core_postgres_data_dev"
echo ""

# Start frontend reminder
echo -e "${YELLOW}📌 Don't forget to start the frontend:${NC}"
echo "  cd frontend"
echo "  npm install"
echo "  PORT=3100 npm run dev"
echo ""