#!/bin/bash

# PRISM Local Development Stop Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping PRISM Development Environment${NC}"
echo "========================================"

# Parse command line arguments
REMOVE_VOLUMES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            REMOVE_VOLUMES=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean    Remove volumes (database data will be lost)"
            echo "  --help     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0           # Stop services, keep data"
            echo "  $0 --clean   # Stop services and remove all data"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Stop services
echo -e "${RED}Stopping services...${NC}"
docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile debug --profile email down

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${RED}Removing volumes...${NC}"
    docker volume rm prism-core_postgres_data_dev prism-core_redis_data_dev 2>/dev/null || true
    echo -e "${GREEN}✅ Volumes removed${NC}"
fi

echo -e "${GREEN}✅ PRISM Development Environment Stopped${NC}"

if [ "$REMOVE_VOLUMES" = false ]; then
    echo ""
    echo -e "${YELLOW}Note: Data has been preserved. Use --clean to remove volumes.${NC}"
fi